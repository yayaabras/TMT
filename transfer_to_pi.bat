@echo off
REM Transfer script for Windows to Raspberry Pi
REM Edit the PI_IP variable below with your Pi's IP address

SET PI_IP=192.168.1.192
SET PI_USER=pi
SET PROJECT_PATH=/home/pi/TFL

echo ===============================================
echo Taxi Tracker - File Transfer to Raspberry Pi
echo ===============================================
echo.

REM Check if scp is available
where scp >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: SCP not found. Please install OpenSSH client or use WinSCP.
    echo You can enable OpenSSH client in Windows Features.
    pause
    exit /b 1
)

echo Target: %PI_USER%@%PI_IP%:%PROJECT_PATH%
echo.

REM Create project directory on Pi
echo Creating project directory on Pi...
ssh %PI_USER%@%PI_IP% "mkdir -p %PROJECT_PATH%"

REM Transfer files
echo Transferring application files...
scp app.py %PI_USER%@%PI_IP%:%PROJECT_PATH%/
scp config.py %PI_USER%@%PI_IP%:%PROJECT_PATH%/
scp wsgi.py %PI_USER%@%PI_IP%:%PROJECT_PATH%/
scp requirements.txt %PI_USER%@%PI_IP%:%PROJECT_PATH%/
scp .env %PI_USER%@%PI_IP%:%PROJECT_PATH%/
scp gunicorn.conf.py %PI_USER%@%PI_IP%:%PROJECT_PATH%/
scp taxi-tracker.service %PI_USER%@%PI_IP%:%PROJECT_PATH%/
scp deploy.sh %PI_USER%@%PI_IP%:%PROJECT_PATH%/
scp README_PI_DEPLOYMENT.md %PI_USER%@%PI_IP%:%PROJECT_PATH%/

REM Transfer templates directory
echo Transferring templates...
scp -r templates %PI_USER%@%PI_IP%:%PROJECT_PATH%/

REM Transfer static files (if they exist)
if exist static (
    echo Transferring static files...
    scp -r static %PI_USER%@%PI_IP%:%PROJECT_PATH%/
)

REM Transfer instance directory (database)
if exist instance (
    echo Transferring database...
    scp -r instance %PI_USER%@%PI_IP%:%PROJECT_PATH%/
)

echo.
echo ===============================================
echo File transfer completed!
echo ===============================================
echo.
echo Next steps:
echo 1. SSH into your Pi: ssh %PI_USER%@%PI_IP%
echo 2. Navigate to project: cd %PROJECT_PATH%
echo 3. Run deployment script: chmod +x deploy.sh && ./deploy.sh
echo.
echo Or run the deployment remotely:
echo ssh %PI_USER%@%PI_IP% "cd %PROJECT_PATH% && chmod +x deploy.sh && ./deploy.sh"
echo.
pause
