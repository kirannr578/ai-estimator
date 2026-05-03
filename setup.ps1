# Construction Plan Estimator - one-shot Windows setup script.
#
# Usage (run from this folder):
#     PowerShell -ExecutionPolicy Bypass -File .\setup.ps1
#
# What it does:
#   1. Detects Python 3.10+ on PATH (or via the `py` launcher).
#      If only the Microsoft Store shim is present it tells you how to fix it.
#   2. Creates a `.venv` virtual environment in this folder.
#   3. Installs everything in requirements.txt.
#   4. Copies .env.example -> .env if you don't have one yet.
#   5. Prints a single command to launch the app.

$ErrorActionPreference = "Stop"

function Find-Python {
    foreach ($name in @("py", "python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        # Skip the Microsoft Store shim (executable lives under WindowsApps and is 0 bytes-ish)
        if ($cmd.Source -like "*WindowsApps*") { continue }
        try {
            $vstr = & $cmd.Source --version 2>&1
            if ($vstr -match "Python\s+(\d+)\.(\d+)") {
                $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 10)) {
                    return @{ Cmd = $cmd.Source; Version = $vstr }
                }
            }
        } catch {}
    }
    return $null
}

Write-Host "==> Looking for Python 3.10+..." -ForegroundColor Cyan
$python = Find-Python
if (-not $python) {
    Write-Host ""
    Write-Host "Python 3.10+ was not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "If you see a 'Microsoft Store' window when you run python, that's"
    Write-Host "Windows' app-execution-alias shim; turn it off OR install real Python:"
    Write-Host ""
    Write-Host "  Option A (winget, recommended):"
    Write-Host "    winget install -e --id Python.Python.3.12"
    Write-Host ""
    Write-Host "  Option B (manual):"
    Write-Host "    https://www.python.org/downloads/windows/"
    Write-Host "    During install, tick 'Add python.exe to PATH'."
    Write-Host ""
    Write-Host "  After installing, close and re-open PowerShell, then re-run this script."
    exit 1
}

Write-Host "Using $($python.Version) at $($python.Cmd)" -ForegroundColor Green

# --- venv -----------------------------------------------------------------
if (-not (Test-Path ".venv")) {
    Write-Host "==> Creating virtual environment .venv ..." -ForegroundColor Cyan
    & $python.Cmd -m venv .venv
} else {
    Write-Host "==> Reusing existing .venv" -ForegroundColor Cyan
}

$venvPython = Join-Path (Resolve-Path ".venv").Path "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "venv Python not found at $venvPython" -ForegroundColor Red
    exit 1
}

# --- pip / deps -----------------------------------------------------------
Write-Host "==> Upgrading pip ..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip > $null

Write-Host "==> Installing requirements.txt (this can take a minute the first time)..." -ForegroundColor Cyan
& $venvPython -m pip install -r requirements.txt

# --- .env -----------------------------------------------------------------
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> Created .env from .env.example - open it and add your API key:" -ForegroundColor Yellow
    Write-Host "       notepad .env"
} else {
    Write-Host "==> .env already exists." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env and set ANTHROPIC_API_KEY or OPENAI_API_KEY:"
Write-Host "       notepad .env"
Write-Host "  2. Activate the venv in your shell:"
Write-Host "       .\.venv\Scripts\Activate.ps1"
Write-Host "  3a. Launch the web UI:"
Write-Host "       streamlit run app.py"
Write-Host "  3b. OR run from the command line on a folder of PDFs:"
Write-Host '       python analyze.py "C:\path\to\GMP#003-Permit-Set" --recursive --no-drawings --out exports\dryrun'
