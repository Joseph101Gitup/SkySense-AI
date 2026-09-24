@echo off
REM =====================================================================
REM  SKYsense AI - Windows Batch Workflow Script
REM  Automates the complete workflow:
REM  VERIFY -> TRAIN -> EVALUATE -> EXPORT -> MIGRATE -> SERVER -> TEST
REM =====================================================================

SETLOCAL ENABLEDELAYEDEXPANSION
SET REPO_ROOT=%~dp0..
CD /D "%REPO_ROOT%"

REM Detect Python executable (prefer virtualenv if present)
IF EXIST "03_AI_Model\.venv\Scripts\python.exe" (
    SET PYTHON="03_AI_Model\.venv\Scripts\python.exe"
) ELSE (
    SET PYTHON=python
)

echo =====================================================================
echo          SKYSENSE AI - WINDOWS AUTOMATED WORKFLOW
echo =====================================================================
echo Using Python: %PYTHON%
echo Repo Root   : %REPO_ROOT%
echo =====================================================================

%PYTHON% scripts\run_workflow.py %*
IF ERRORLEVEL 1 (
    echo [!] Workflow execution failed.
    EXIT /B 1
)

echo [OK] Windows workflow finished successfully.
EXIT /B 0
