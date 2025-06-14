@echo off
if exist "pyenv\.pyenv" (
    echo Fast deleting existing pyenv\.pyenv directory...
    mkdir empty_temp 2>nul
    robocopy empty_temp "pyenv\.pyenv" /mir /nfl /ndl /njh /njs /nc /ns /np
    rmdir /s /q "pyenv\.pyenv" 2>nul
    rmdir empty_temp 2>nul
)

cd pyenv/scripts/windows

pyenv0 && pyenv1 && pyenv2

cd ../../..

cls