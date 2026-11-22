@echo off
setlocal

set "REPO_ROOT=%~dp0.."
set "HF_CLI_PATH=%REPO_ROOT%\.hf_cli"
set "HF_EXE=%HF_CLI_PATH%\bin\hf.exe"
set "PROJECT_HF_HOME=%REPO_ROOT%\.hf_cache"

if not exist "%HF_EXE%" (
  echo Project-local Hugging Face CLI executable not found: %HF_EXE% 1>&2
  exit /b 1
)

if defined PYTHONPATH (
  set "PYTHONPATH=%HF_CLI_PATH%;%PYTHONPATH%"
) else (
  set "PYTHONPATH=%HF_CLI_PATH%"
)

if not defined HF_HOME set "HF_HOME=%PROJECT_HF_HOME%"
if not defined HF_HUB_DISABLE_SYMLINKS_WARNING set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
if not defined HTTP_PROXY set "HTTP_PROXY=http://127.0.0.1:10808"
if not defined HTTPS_PROXY set "HTTPS_PROXY=http://127.0.0.1:10808"

"%HF_EXE%" %*
exit /b %ERRORLEVEL%
