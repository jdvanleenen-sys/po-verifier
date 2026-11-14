# Start the PO Checker phone app on this laptop.
#   powershell -ExecutionPolicy Bypass -File app\start.ps1 -Folder "<the contractor's folder>"
# Sets up the app's Python environment the first time, checks Claude Code is there, then starts the
# server and prints the link to open on the phone.
param([Parameter(Mandatory = $true)][string]$Folder, [int]$Port = 8000)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "First start: setting up the app's Python environment."
    python -m venv --system-site-packages (Join-Path $repo ".venv")
    & $python -m pip install --quiet -r (Join-Path $PSScriptRoot "requirements.txt")
}
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    throw "Claude Code (claude) is not on the PATH. The read needs it. Install it and sign in, then start again."
}
if (-not (Test-Path (Join-Path $Folder "reference\contractor.md"))) {
    throw "$Folder is not a set-up PO Verifier folder (no reference\contractor.md)."
}
Write-Host "Leave this window open while the app is in use. Ctrl+C stops it."
& $python (Join-Path $PSScriptRoot "server.py") --folder $Folder --port $Port
