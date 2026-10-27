@echo off
REM 윈도우에서 두 번 눌러 실행합니다. 터미널을 몰라도 됩니다.
setlocal
cd /d "%~dp0"

where py >nul 2>&1 && (py -3 START.py %* & goto done)
where python >nul 2>&1 && (python START.py %* & goto done)
where python3 >nul 2>&1 && (python3 START.py %* & goto done)

echo.
echo 파이썬을 찾지 못했습니다.
echo 이 컴퓨터에 파이썬이 설치되어 있지 않은 것입니다. 강사에게 말씀하세요.
echo.

:done
echo.
pause
