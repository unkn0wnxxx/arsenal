import struct

hex_str = input("Paste the hex SID (with or without 0x): ").strip().replace("0x", "").replace(" ", "")
sid_bytes = bytes.fromhex(hex_str)

rev = sid_bytes[0]
sub_count = sid_bytes[1]
auth = int.from_bytes(sid_bytes[2:8], 'big')

parts = [rev, auth]
for i in range(sub_count):
    sub = struct.unpack_from('<I', sid_bytes, 8 + 4*i)[0]
    parts.append(sub)

full_sid = "S-" + "-".join(str(p) for p in parts)
domain_sid = "S-" + "-".join(str(p) for p in parts[:-1])  # drop RID
rid = parts[-1]

print(f"Full SID: {full_sid}")
print(f"Domain SID: {domain_sid}")
print(f"RID: {rid}")
