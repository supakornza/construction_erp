param(
    [string]$Message = "Update dashboard performance and production settings",
    [string]$Branch = "main",
    [switch]$Remote,
    [string]$RemoteHost = "supakorn1997@ssh.pythonanywhere.com",
    [string]$RemoteProjectDir = "/home/supakorn1997/construction_erp"
)

$ErrorActionPreference = "Stop"

function Run-Step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    Write-Host ""
    Write-Host "==> $Label" -ForegroundColor Cyan
    & $Command
}

Run-Step "Checking current branch" {
    $currentBranch = (git branch --show-current).Trim()
    if ($currentBranch -ne $Branch) {
        throw "Current branch is '$currentBranch'. Switch to '$Branch' before deploying."
    }
}

Run-Step "Showing git status" {
    git status --short
}

Run-Step "Staging changes" {
    git add .
}

Run-Step "Creating commit if needed" {
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "No staged changes. Skipping commit."
    } else {
        git commit -m $Message
    }
}

Run-Step "Pushing to origin/$Branch" {
    git push origin $Branch
}

if ($Remote) {
    Run-Step "Deploying on PythonAnywhere via SSH" {
        ssh $RemoteHost "cd $RemoteProjectDir && bash scripts/deploy-pythonanywhere.sh"
    }
} else {
    Write-Host ""
    Write-Host "Local push complete." -ForegroundColor Green
    Write-Host "To deploy on PythonAnywhere, run:" -ForegroundColor Yellow
    Write-Host "  cd $RemoteProjectDir && bash scripts/deploy-pythonanywhere.sh"
    Write-Host ""
    Write-Host "Or run this local script with -Remote if SSH access is configured:"
    Write-Host "  .\scripts\deploy-local.ps1 -Remote"
}
