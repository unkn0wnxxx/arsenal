# How to compile nim reverse shells

---

To evade AV those compiled shells are very secure.

```
python3 -m venv myenv
source myenv/bin/activate
curl https://nim-lang.org/choosenim/init.sh -sSf | sh
echo 'export PATH=~/.nimble/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```


```
nim c -d:mingw --app:gui --opt:speed -o:spoofer-scheduler.exe rev_shell.nim 
```
