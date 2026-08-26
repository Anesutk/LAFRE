# PowerShell helper: create venv and install requirements
# Usage: Open PowerShell in the backend folder and run: .\venv_setup.ps1

$venvPath = "$PWD\.venv"
if (-Not (Test-Path $venvPath)) {
    python -m venv $venvPath
}
$activate = Join-Path $venvPath "Scripts/Activate.ps1"
Write-Host "Activating venv: $activate"
& $activate
Write-Host "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "Setup complete. To activate later: .\ .venv\Scripts\Activate.ps1"
