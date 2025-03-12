@echo off

adb devices -l

appium -a 127.0.0.1 -p 4723 -pa /wd/hub -g appium_server.log

pause