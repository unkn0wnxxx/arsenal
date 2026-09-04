# How to compile

---

## PoC

##### If not installed

```
apt-get install g++-mingw-w64
```


```
i686-w64-mingw32-g++ shell.cpp -o taskkill.exe -lws2_32 -s -ffunction-sections -fdata-sections -Wno-write-strings -fno-exceptions -fmerge-all-constants -static-libstdc++ -static-libgcc
```
