# Packt die Projektdateien in ein ZIP und schreibt die SHA256-Prüfsumme daneben.
# Aufruf in der Pipeline:  pwsh -File ci/Package.ps1 -Version "$CI_COMMIT_SHORT_SHA"
# Ergebnis: dist/banana-project-<Version>.zip und dist/banana-project-<Version>.zip.sha256
param([string]$Version = 'local')

# Bei jedem Fehler sofort abbrechen; ein halbes ZIP soll es nicht geben.
$ErrorActionPreference = 'Stop'

# Projektordner = eine Ebene über ci/
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Zielordner dist/ anlegen (das Artifact des Jobs).
New-Item -ItemType Directory -Path dist -Force | Out-Null
$archive = "dist/banana-project-$Version.zip"

# Diese Dateien und Ordner kommen ins ZIP.
Compress-Archive -Path README.md, ListFiles.ps1, ci, tests -DestinationPath $archive -Force

# Prüfsumme berechnen und als eigene Datei ablegen.
$hash = (Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  banana-project-$Version.zip" | Set-Content "$archive.sha256"

Write-Output "PACKAGE_CREATED $archive SHA256=$hash"
