# gMSADumper-ng

## tl;dr
In modern AD you often need aes key instead of just NTLM. I noticed netexec --gmsa flag only grabs ntlm. gMSADumper grabs aes & ntlm, but OG tool didn't have fallback ldap bind methods and caused some labs to fail with the tool. I made a patch for fallback auth and opened a PR and made this new repo for future changes

## Description

gMSADumper-NG parses and prints managed service account password blobs (msDS-ManagedPassword) that the authenticated user can read. The tool will try multiple LDAP bind methods automatically to handle a variety of domain controller configurations.

## Important notes

* For lab convenience the script disables TLS certificate validation when using LDAPS or StartTLS. Change the Tls settings if you must enforce strict certificate validation.
* The script tries several bind styles automatically. If you prefer a single bind style, pass appropriate arguments or edit the script.

## Features

* Detects and tries multiple LDAP bind styles automatically:

  * NTLM over LDAPS using NETBIOS\username
  * UPN SIMPLE over LDAPS using user@dnsdomain
  * NTLM with StartTLS on ldap://
  * UPN SIMPLE with StartTLS on ldap://
* Parses msDS-ManagedPassword blobs and prints NTLM, AES128 and AES256 keys
* Prints which users or groups can read each gMSA password
* Keeps Kerberos authentication path intact for environments using Kerberos

## Usage

Basic usage with username and password:

```bash
python3 gMSADumper-NG.py -u USER -p 'PASSWORD' -d domain.local
```

Specifying a particular LDAP server or host:

```bash
python3 gMSADumper-NG.py -u USER -p 'PASSWORD' -d domain.local -l dc01.domain.local
```

Pass NTLM hash instead of password:

```bash
python3 gMSADumper-NG.py -u USER -p LMHASH:NTHASH -d domain.local -l dc01.domain.local
```

Use Kerberos authentication:

```bash
python3 gMSADumper-NG.py -k -d domain.local -l dc01.domain.local
```

Notes:

* If the domain has an unusual UPN suffix, try passing `-d` with the NetBIOS name or the UPN suffix that works in your environment.
* If LDAPS or StartTLS are required by the DC, the tool will attempt those automatically. If you have strict CA validation requirements, update the Tls settings in the script.

## Example output

* A list of accounts or groups that can read the password for each gMSA
* The NTLM hash and AES keys formatted for use in common tools

## Security and legal

Only use this tool where you have authorization. Accessing or extracting credentials without permission is illegal and unethical.

## Development status and TODO

* TODO items for future contributors:

  * Add optional strict TLS validation and CA bundle support
  * Add an option to prefer UPN or NetBIOS bind styles
  * Improve error messages and logging

Contributions are welcome.

## Previous Work and Acknowledgements
Original project by @micahvandeusen

Uses Impacket structures and ideas from community tools
