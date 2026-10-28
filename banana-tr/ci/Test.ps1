# Führt die Tests des Projekts mit Pester aus und meldet das Ergebnis über den Exit-Code.
# Aufruf in der Pipeline:  pwsh -File ci/Test.ps1
# Mit -ForceFailure scheitert ein Test absichtlich (zum Vorführen eines roten Jobs).
param([switch]$ForceFailure)

# Bei jedem Fehler sofort abbrechen, statt still weiterzulaufen.
$ErrorActionPreference = 'Stop'

# Pester ist das Testframework für PowerShell; die Version ist im CI-Image installiert.
Import-Module Pester -RequiredVersion 5.7.1

# Die Testdatei liest diese Umgebungsvariable (Test-Gate).
$env:BANANA_FORCE_FAILURE = if ($ForceFailure) { '1' } else { '0' }

# Welche Testdatei laufen soll und wie ausführlich das Log wird.
$config = New-PesterConfiguration
$config.Run.Path = Join-Path $PSScriptRoot '../tests/BananaProject.Tests.ps1'
$config.Run.PassThru = $true           # Ergebnis als Objekt zurückgeben, damit wir es auswerten können
$config.Output.Verbosity = 'Detailed'  # jeden Test einzeln im Joblog anzeigen

# Tests ausführen.
$run = Invoke-Pester -Configuration $config

# Kurzergebnis im Joblog.
Write-Output "TESTS: total=$($run.TotalCount) passed=$($run.PassedCount) failed=$($run.FailedCount)"

# Exit-Code 1 macht den Job rot: wenn ein Test scheitert oder gar keiner gelaufen ist.
if ($run.TotalCount -eq 0 -or $run.Result -ne 'Passed') { exit 1 }
exit 0
