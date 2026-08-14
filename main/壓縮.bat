@echo off
chcp 65001 >nul
title ZIP Compression
color 0B

echo ===================================================================
echo    Creating ZIP Archive...
echo ===================================================================
echo.

set ZIP_NAME=ChroLens_Mimic.zip
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; $src = Join-Path (Get-Location).Path 'dist\ChroLens_Mimic'; $dst = Join-Path (Get-Location).Path 'dist\%ZIP_NAME%'; if (Test-Path $dst) { Remove-Item $dst -Force }; [System.IO.Compression.ZipFile]::CreateFromDirectory($src, $dst, [System.IO.Compression.CompressionLevel]::Fastest, $false); Write-Host 'ZIP created successfully at dist\%ZIP_NAME%' -ForegroundColor Green"

echo.
echo ZIP archive created. You can close this window.
pause
