@echo off
REM Double-click to run. ASCII only, CRLF line endings -- see below.
REM  * Korean text must NOT live here: cmd.exe reads .bat in the OEM
REM    codepage, so UTF-8 Hangul turns into mojibake AND breaks parsing.
REM  * LF-only endings make cmd.exe swallow the first character of a
REM    line (echo. becomes cho.). The repo pins CRLF via .gitattributes.
chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

where py >nul 2>&1
if not errorlevel 1 goto usepy
where python >nul 2>&1
if not errorlevel 1 goto usepython
where python3 >nul 2>&1
if not errorlevel 1 goto usepython3
goto nopython

:usepy
py -3 "%~dp0START.py" %*
goto done

:usepython
python "%~dp0START.py" %*
goto done

:usepython3
python3 "%~dp0START.py" %*
goto done

:nopython
echo.
echo [!] Python was not found on this PC.
echo     Please ask your instructor. (Python 3.10 or newer)
echo.

:done
echo.
echo Press any key to close this window...
pause >nul
