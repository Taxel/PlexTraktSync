@echo off
color 04
echo Killing any running versions of this script...
taskkill /F /FI "WindowTitle eq  Hawke.one - Trakt Sync - Setup" /T
taskkill /F /FI "WindowTitle eq  Hawke.one - Trakt Sync" /T

title Hawke.one - Trakt Sync - Setup
cls

echo -----------------------------------------------------------------------------------
echo  Hawke.one - Trakt Sync - Setup (beta 2.0)
echo -----------------------------------------------------------------------------------
echo This project stores PyTrakt API keys (no passwords) in plain text on your system.
echo If you do not want to have a file containing these on your system, you can not use this project.
echo.
echo The entire project is open source (just open the data folder, it's all there),
echo and is based upon the work of Taxel: https://github.com/Taxel/PlexTraktSync
echo.
SET /P APICONT="Would you like to continue? ([Y]/N)?"
IF /I "%APICONT%" EQU "N" GOTO :ENDIT

echo Checking for Python...
:: Check for Python Installation
py --version 2>NUL
if errorlevel 1 goto errorNoPython
echo.

IF NOT EXIST "%cd%\Hawke.one Trakt Sync.lnk" goto :START
echo WARNING: Setup has already been run!
echo Continuing will reset the configuration (including scheduled tasks and startup routines).
echo.
SET /P RESETAPP="Reset to default values and setup from scratch? (Y/[N])?"
IF /I "%RESETAPP%" NEQ "Y" GOTO :ENDIT
schtasks /delete /tn "Plex Trakt Sync" /f >nul 2>&1
del "%userprofile%\Start Menu\Programs\Startup\Hawke.one Trakt Sync.lnk" /f >nul 2>&1
del "%userprofile%\Desktop\Hawke.one Trakt Sync.lnk" /f >nul 2>&1
del "data\.env" /f >nul 2>&1
del ".pytrakt.json" /f >nul 2>&1
echo Restoring default settings... Done!




:START
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%cd%\Hawke.one Trakt Sync.lnk');$s.TargetPath='%cd%\data\hawke.one trakt sync.bat';$s.IconLocation='%cd%\data\trakt.ico';$s.Save()"
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%cd%\data\Sync Plex Server and Trakt.lnk');$s.TargetPath='%cd%\data\hawke.one trakt sync.bat';$s.IconLocation='%cd%\data\trakt.ico';$s.Save()"


echo.
SET /P SCHEDULED=Would you like to schedule sync to run daily? (Y/[N])?
IF /I "%SCHEDULED%" NEQ "Y" GOTO :NOSCHEDULE
SET /P SCHEDULED_TIME=What time would you like the sync to run (Use 24 hour time. eg: 01:00, 23:42)?
SCHTASKS /CREATE /SC DAILY /TN "Plex Trakt Sync" /TR "%cd%\data\Scheduled Task - Sync Plex Server and Trakt.bat" /ST "%SCHEDULED_TIME%"
echo.

:NOSCHEDULE
SET /P STARTUP=Would you like to schedule sync to run on system start up? (Y/[N])?
IF /I "%STARTUP%" NEQ "Y" GOTO :NOSTARTUP
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%userprofile%\Start Menu\Programs\Startup\Hawke.one Trakt Sync.lnk');$s.TargetPath='%cd%\data\hawke.one trakt sync.bat';$s.IconLocation='%cd%\data\trakt.ico';$s.Save()"
echo Creating startup routine... Done!
echo.

:NOSTARTUP
SET /P DESKTOPQ=Would you like to create a desktop shortcut to run sync manually? (Y/[N])?
IF /I "%DESKTOPQ%" NEQ "Y" GOTO :NODESKTOP
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%userprofile%\Desktop\Hawke.one Trakt Sync.lnk');$s.TargetPath='%cd%\data\hawke.one trakt sync.bat';$s.IconLocation='%cd%\data\trakt.ico';$s.Save()"
echo Creating desktop shortcut... Done!
echo.

:NODESKTOP
echo Once fully configured hawke.one will now sync with Plex:
IF /I "%SCHEDULED%" EQU "Y" echo.    * Automatically at %SCHEDULED_TIME%
IF /I "%STARTUP%" EQU "Y" echo.    * Automatically at system startup
IF /I "%DESKTOPQ%" EQU "Y" echo.    * Manually using the shortcut on your desktop
echo.    * Manually using the shortcut created at %cd%\Hawke.one Trakt Sync
echo.

echo Press any key to continue with setup...
echo.
pause > nul
echo Installing Python requirements...
pip install -r data\requirements.txt
Pushd "%~dp0data"
call "hawke.one trakt sync.bat"
goto :ENDIT

:errorNoPython
echo You will need to download and install Python to use this project: https://www.python.org/downloads
echo Please download and install Python, then restart this project.
echo Press any key to exit
echo.
pause > nul
goto :ENDIT

:NO_WRITE_ACCESS
echo AN ERROR HAS OCCCURED! 
echo Please ensure that you have read / write access to the current directory, then restart setup.
echo Press any key to exit
echo.
pause > nul


:ENDIT