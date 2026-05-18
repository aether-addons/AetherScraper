@echo off
setlocal

rem Build Kodi-installable zip for script.module.aetherscraper.
rem Put this BAT beside script.module.aetherscraper folder. Run on Windows.

set "ADDON_ID=script.module.aetherscraper"
set "VERSION=0.1.0"
set "ROOT=%~dp0"
set "ADDON_DIR=%ROOT%%ADDON_ID%"
set "DIST_DIR=%ROOT%dist"
set "ZIP_PATH=%DIST_DIR%\%ADDON_ID%-%VERSION%.zip"
set "PS1=%TEMP%\aetherscraper_package_%RANDOM%%RANDOM%.ps1"

if not exist "%ADDON_DIR%\addon.xml" (
  echo ERROR: Missing "%ADDON_DIR%\addon.xml"
  echo Put this BAT beside the "%ADDON_ID%" folder, then run again.
  pause
  exit /b 1
)

if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"

> "%PS1%" echo $ErrorActionPreference = 'Stop'
>> "%PS1%" echo Add-Type -AssemblyName System.IO.Compression
>> "%PS1%" echo Add-Type -AssemblyName System.IO.Compression.FileSystem
>> "%PS1%" echo $addonId = '%ADDON_ID%'
>> "%PS1%" echo $root = [IO.Path]::GetFullPath('%ROOT%')
>> "%PS1%" echo $addon = Join-Path $root $addonId
>> "%PS1%" echo $zip = [IO.Path]::GetFullPath('%ZIP_PATH%')
>> "%PS1%" echo $excludeDirs = @('__pycache__','.ruff_cache','.git','.venv','venv')
>> "%PS1%" echo $excludeExt = @('.pyc','.pyo')
>> "%PS1%" echo if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
>> "%PS1%" echo $archive = [IO.Compression.ZipFile]::Open($zip, [IO.Compression.ZipArchiveMode]::Create)
>> "%PS1%" echo try {
>> "%PS1%" echo   Get-ChildItem -LiteralPath $addon -Recurse -Force -File ^| ForEach-Object {
>> "%PS1%" echo     $rel = $_.FullName.Substring($addon.Length).TrimStart([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
>> "%PS1%" echo     $parts = $rel -split '[\\/]'
>> "%PS1%" echo     if ($parts ^| Where-Object { $excludeDirs -contains $_ }) { return }
>> "%PS1%" echo     if ($excludeExt -contains $_.Extension.ToLowerInvariant()) { return }
>> "%PS1%" echo     $entryName = ($addonId + '/' + (($rel -split '[\\/]') -join '/'))
>> "%PS1%" echo     [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $_.FullName, $entryName, [IO.Compression.CompressionLevel]::Optimal) ^| Out-Null
>> "%PS1%" echo   }
>> "%PS1%" echo } finally { $archive.Dispose() }
>> "%PS1%" echo $archive = [IO.Compression.ZipFile]::OpenRead($zip)
>> "%PS1%" echo try {
>> "%PS1%" echo   $needed = $addonId + '/addon.xml'
>> "%PS1%" echo   $names = @($archive.Entries ^| ForEach-Object { $_.FullName.Replace('\\','/') })
>> "%PS1%" echo   if ($names -notcontains $needed) { Write-Host 'Zip entries:'; $names ^| Select-Object -First 50 ^| ForEach-Object { Write-Host $_ }; throw ('Zip invalid: missing ' + $needed) }
>> "%PS1%" echo   $bad = @($names ^| Where-Object { -not $_.StartsWith($addonId + '/') })
>> "%PS1%" echo   if ($bad.Count -gt 0) { throw ('Zip invalid: bad top-level entry ' + $bad[0]) }
>> "%PS1%" echo   Write-Host ('Built and verified: ' + $zip)
>> "%PS1%" echo } finally { $archive.Dispose() }

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
set "ERR=%ERRORLEVEL%"
del /f /q "%PS1%" >nul 2>nul

if not "%ERR%"=="0" (
  echo.
  echo ERROR: Packaging failed.
  pause
  exit /b %ERR%
)

echo.
echo Done. Install this zip in Kodi:
echo %ZIP_PATH%
pause
