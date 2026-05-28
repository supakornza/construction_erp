# Upload and deploy Construction ERP to VPS
# Run from project root: .\scripts\upload_and_deploy.ps1

$VPS_IP = "187.77.141.145"
$VPS_USER = "root"
$PROJECT_DIR = Split-Path -Parent $PSScriptRoot
$REMOTE_TMP = "/tmp/construction_erp"

Write-Host "=== Uploading Construction ERP to VPS ===" -ForegroundColor Cyan

# Check SSH is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Error "SSH not found. Install OpenSSH or Git Bash."
    exit 1
}

Write-Host "[1/3] Uploading project files via rsync/scp..."

# Use scp to copy (Windows-friendly)
$exclude_file = "$env:TEMP\rsync_exclude.txt"
@"
venv/
.git/
__pycache__/
*.pyc
.env
db.sqlite3
db.sqlite3.bak*
.claude/
staticfiles/
logs/
screenshots/
*.png
"@ | Out-File -FilePath $exclude_file -Encoding utf8

# Create archive excluding unnecessary files
$archive = "$env:TEMP\construction_erp.tar.gz"
Write-Host "  Creating archive..."

# Use tar (available on Windows 10+)
Push-Location $PROJECT_DIR
tar --exclude="./venv" --exclude="./.git" --exclude="./__pycache__" `
    --exclude="./.claude" --exclude="./staticfiles" --exclude="./logs" `
    --exclude="./db.sqlite3" --exclude="./db.sqlite3.bak*" `
    --exclude="./.env" --exclude="./screenshots" --exclude="*.pyc" `
    -czf $archive . 2>$null
Pop-Location

Write-Host "  Archive created: $archive"

Write-Host "[2/3] Uploading to VPS..."
scp -o StrictHostKeyChecking=no $archive "${VPS_USER}@${VPS_IP}:/tmp/construction_erp.tar.gz"

Write-Host "[3/3] Extracting and deploying on VPS..."
$remote_commands = @"
set -e
echo 'Extracting files...'
rm -rf /tmp/construction_erp
mkdir -p /tmp/construction_erp
tar -xzf /tmp/construction_erp.tar.gz -C /tmp/construction_erp
echo 'Running deploy script...'
bash /tmp/construction_erp/scripts/deploy_vps.sh
"@

ssh -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_IP}" $remote_commands

Write-Host ""
Write-Host "Done! Visit: http://$VPS_IP" -ForegroundColor Green
Write-Host ""
Write-Host "To create admin user, run:" -ForegroundColor Yellow
Write-Host "  ssh root@$VPS_IP"
Write-Host "  cd /var/www/construction_erp"
Write-Host "  DJANGO_SETTINGS_MODULE=config.settings.production venv/bin/python manage.py createsuperuser"
