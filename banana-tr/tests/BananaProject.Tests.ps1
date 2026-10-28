# Tests für ListFiles.ps1, geschrieben für Pester.
# Jeder It-Block ist ein Test; Should prüft das erwartete Ergebnis.

BeforeAll {
    # Pfad zum getesteten Skript (eine Ebene über tests/).
    $script:listScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'ListFiles.ps1'
}

Describe 'ListFiles' {
    It 'liefert für ein leeres Verzeichnis keine Zeile' {
        $folder = Join-Path $TestDrive 'empty'
        New-Item -ItemType Directory -Path $folder | Out-Null
        @(& $listScript -Path $folder) | Should -HaveCount 0
    }
    It 'meldet einen ungültigen Pfad als Fehler' {
        { & $listScript -Path (Join-Path $TestDrive 'missing') } | Should -Throw
    }
    It 'zeigt den Dateinamen und die Bytezahl' {
        $folder = Join-Path $TestDrive 'one'
        New-Item -ItemType Directory -Path $folder | Out-Null
        [IO.File]::WriteAllText((Join-Path $folder 'banana.txt'), 'banana')
        @(& $listScript -Path $folder)[0] | Should -Be 'banana.txt - 6 Bytes'
    }
    It 'sortiert Dateien und lässt Unterverzeichnisse aus' {
        $folder = Join-Path $TestDrive 'many'
        New-Item -ItemType Directory -Path $folder | Out-Null
        [IO.File]::WriteAllText((Join-Path $folder 'z.txt'), 'z')
        [IO.File]::WriteAllText((Join-Path $folder 'a.txt'), 'a')
        New-Item -ItemType Directory -Path (Join-Path $folder 'subdir') | Out-Null
        $rows = @(& $listScript -Path $folder)
        $rows | Should -HaveCount 2
        $rows[0] | Should -Be 'a.txt - 1 Bytes'
    }
}

Describe 'Test-Gate' {
    # Scheitert nur, wenn ci/Test.ps1 mit -ForceFailure aufgerufen wurde.
    It 'scheitert absichtlich bei -ForceFailure' {
        $env:BANANA_FORCE_FAILURE | Should -Not -Be '1'
    }
}
