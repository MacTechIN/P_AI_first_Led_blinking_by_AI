@echo off
REM Double-click to run. ASCII only, CRLF endings.
REM  * No Korean here: cmd.exe reads .bat in the OEM codepage.
REM  * No PYTHONIOENCODING / chcp: Python writes to a real Windows
REM    console through WriteConsoleW, which is Unicode-safe already.
REM    Setting PYTHONIOENCODING turns that off and sends bytes through
REM    the codepage instead -- that is how Hangul got mangled once.
setlocal
cd /d "%~dp0"

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
