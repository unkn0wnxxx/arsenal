# RCE with .config

---

We can utilize an web.config file which is an default file on Windows Servers in order to execute .aspx commands on the target.

## Situation

If we have file upload mechanics and found out that .config files can be uploaded we can get RCE through that.

Used the web.config file in the current directory in order to download an .ps1 rce which immediatly get's executed.


