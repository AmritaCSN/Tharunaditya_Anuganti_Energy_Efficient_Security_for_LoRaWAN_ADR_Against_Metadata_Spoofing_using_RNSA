@echo off
REM ============================================================
REM  quick_start.bat
REM  One-click launcher for OMNeT++ MinGW shell
REM  Place this file anywhere — double-click to open environment
REM ============================================================

SET OMNETPP_ROOT=C:\omnetpp

IF NOT EXIST "%OMNETPP_ROOT%\mingwenv.cmd" (
    echo [ERROR] OMNeT++ not found at %OMNETPP_ROOT%
    echo Please extract omnetpp-6.0.3-windows-x86_64.zip to C:\omnetpp
    pause
    exit /b 1
)

echo ============================================================
echo  Opening OMNeT++ MinGW Build Environment
echo  OMNeT++ Root: %OMNETPP_ROOT%
echo ============================================================
echo.
echo NOTE: All builds (./configure, make, git clone) must be
echo       done inside this shell, NOT in regular PowerShell.
echo.

call "%OMNETPP_ROOT%\mingwenv.cmd"
