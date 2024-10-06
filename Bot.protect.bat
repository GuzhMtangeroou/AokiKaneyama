@echo off
set botfile=main.py目录
set basefile=Onebot实现端目录
set botpath=bot工作目录
set basepath=Onebot实现端工作目录
set sleeptime=15

:start

tasklist|find /i "Lagrange.OneBot.exe"    
if %errorlevel%==0 (    
echo Base is running
) else (    
echo Base exited,restarting...
cd %basepath%
start %basefile%
)

tasklist|find /i "Python.exe"    
if %errorlevel%==0 (    
echo Bot is running
) else (    
echo Bot exited,restarting...
cd %botpath%
start %botfile%
)

choice /t %sleeptime% /d y /n >nul
goto start