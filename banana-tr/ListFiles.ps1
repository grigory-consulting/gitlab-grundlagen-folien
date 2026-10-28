# Gibt alle Dateien eines Ordners mit ihrer Größe aus, sortiert nach Namen.
# Aufruf:  pwsh -File ListFiles.ps1 -Path <Ordner>
param([string]$Path = '.')

Get-ChildItem -LiteralPath $Path -File -ErrorAction Stop |   # nur Dateien, keine Ordner
    Sort-Object -Property Name |                              # aufsteigend nach Namen
    ForEach-Object { '{0} - {1} Bytes' -f $_.Name, $_.Length }  # Zeile "name - größe Bytes"