@echo off
setlocal enabledelayedexpansion

for /f "delims=" %%a in ('dir /s /b ..\..\ ^| findstr \.log$') do (echo %%a)
for /f "delims=" %%a in ('dir /s /b ..\..\logs\ ^| findstr \.png$') do (echo %%a)
pause
for /f "delims=" %%a in ('dir /s /b ..\..\ ^| findstr \.log$') do (del /f /q %%a)

for /f "delims=" %%a in ('dir /s /b ..\..\logs\ ^| findstr \.png$') do (del /f /q %%a)
pause