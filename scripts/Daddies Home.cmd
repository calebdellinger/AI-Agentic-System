@echo off
REM "Daddies Home" launcher - forwards to PowerShell script.
setlocal
set "_ROOT=%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%_ROOT%\scripts\daddies-home.ps1" %*
