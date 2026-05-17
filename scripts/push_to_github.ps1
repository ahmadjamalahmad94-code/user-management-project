#!/usr/bin/env pwsh
# push_to_github.ps1 - PowerShell push helper for HobeHub.
# Usage:
#   .\scripts\push_to_github.ps1
#   .\scripts\push_to_github.ps1 "your commit message"

param(
    [string]$Message = "feat: Control Hub + AJAX live search + RADIUS kill-switch + various improvements"
)

# Go to repo root (parent of scripts/)
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# Remove stale index lock if any
if (Test-Path ".git\index.lock") {
    Remove-Item -Force ".git\index.lock"
    Write-Host "Removed stale .git/index.lock" -ForegroundColor Yellow
}

Write-Host "=== Git remote ===" -ForegroundColor Cyan
git remote -v
Write-Host ""

Write-Host "=== Adding all changes ===" -ForegroundColor Cyan
git add -A

Write-Host ""
Write-Host "=== Staged files ===" -ForegroundColor Cyan
git diff --cached --name-status

Write-Host ""
Write-Host "=== Commit message ===" -ForegroundColor Cyan
Write-Host "  $Message"
Write-Host ""

git commit -m "$Message"
if ($LASTEXITCODE -ne 0) {
    Write-Host "No changes to commit or commit failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Pushing to origin/main ===" -ForegroundColor Cyan
git push origin main

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "Check: https://github.com/ahmadjamalahmad94-code/HobeHub"
