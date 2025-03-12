@echo off

TASKKILL /F /IM node.exe
::netshta -a -o | findstr 4723 | awk '{print $1,$5}' | foreach { & "C:\Program Files\Windows NT\Accessories\netsh.exe" interface port set dynamic tcp start=0 end=4722 num=1 mode=close }
pause