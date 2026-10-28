@echo off
REM Encoding diagnostic. ASCII only, CRLF endings.
REM Run this when Hangul comes out garbled. Show the WHOLE output.
setlocal
cd /d "%~dp0"

set "PYEXE="
where py >nul 2>&1
if not errorlevel 1 set "PYEXE=py -3"
if defined PYEXE goto found
where python >nul 2>&1
if not errorlevel 1 set "PYEXE=python"
if defined PYEXE goto found
where python3 >nul 2>&1
if not errorlevel 1 set "PYEXE=python3"
if defined PYEXE goto found
echo [!] Python was not found. Nothing else to check.
goto end

:found
echo ===== 1. console codepage =====
chcp
echo.
echo ===== 2. python =====
echo using: %PYEXE%
%PYEXE% -c "import sys,locale;print('ver',sys.version.split()[0]);print('stdout',sys.stdout.encoding);print('fs',sys.getfilesystemencoding());print('locale',locale.getpreferredencoding())"
echo.
echo ===== 3. TEST A  (plain - this is how START.bat runs) =====
%PYEXE% -c "print('A: \uac00\ub098\ub2e4 \ud55c\uae00')"
echo.
echo ===== 4. TEST B  (with PYTHONIOENCODING=utf-8) =====
set "PYTHONIOENCODING=utf-8"
%PYEXE% -c "print('B: \uac00\ub098\ub2e4 \ud55c\uae00')"
set "PYTHONIOENCODING="
echo.
echo ===== 5. TEST C  (with chcp 65001) =====
chcp 65001
%PYEXE% -c "print('C: \uac00\ub098\ub2e4 \ud55c\uae00')"
echo.
echo Each TEST should read:  ga na da  han geul  in Hangul.
echo Tell the instructor which of A / B / C were readable.

:end
echo.
echo Press any key to close this window...
pause >nul
