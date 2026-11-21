# MIT License
# Copyright (c) 2026 yin-kang83
#
# Windows built-in OCR (Windows.Media.Ocr) for one PNG image. Offline; no network.
# Usage:
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File windows_ocr.ps1 -ImagePath <png> -OutFile <json> [-Language zh-Hans-CN]
# Output JSON: ok/language/text/line_count/width/height/elapsed_ms/error
param(
    [Parameter(Mandatory = $true)][string]$ImagePath,
    [Parameter(Mandatory = $true)][string]$OutFile,
    [string]$Language = "zh-Hans-CN"
)

$ErrorActionPreference = "Stop"
$result = [ordered]@{ ok = $false; language = $Language; text = ""; line_count = 0; width = 0; height = 0; elapsed_ms = 0; error = "" }
$started = [System.Diagnostics.Stopwatch]::StartNew()

function Write-ResultJson {
    param([string]$Path, $Object)
    $json = $Object | ConvertTo-Json -Depth 6 -Compress
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $json, $utf8)
}

try {
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
    $null = [Windows.Globalization.Language, Windows.Foundation, ContentType = WindowsRuntime]
    $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
    $null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime]
    $null = [Windows.Storage.FileAccessMode, Windows.Foundation, ContentType = WindowsRuntime]

    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq "AsTask" -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq "IAsyncOperation``1"
    })[0]

    function Await-Operation($operation, $resultType) {
        $task = $asTask.MakeGenericMethod($resultType).Invoke($null, @($operation))
        $task.Wait()
        return $task.Result
    }

    $engine = $null
    foreach ($tag in @($Language, "zh-Hans-CN", "zh-CN")) {
        if ($null -eq $engine) {
            $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new($tag))
        }
    }
    if ($null -eq $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
    if ($null -eq $engine) { throw "No OCR language pack available" }

    if (-not (Test-Path -LiteralPath $ImagePath)) { throw "Image not found" }
    $imageFile = [Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path -LiteralPath $ImagePath).Path)
    $file = Await-Operation $imageFile ([Windows.Storage.StorageFile])
    $streamOp = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = Await-Operation $streamOp ([Windows.Storage.Streams.IRandomAccessStream])
    $decoderOp = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = Await-Operation $decoderOp ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmapOp = $decoder.GetSoftwareBitmapAsync()
    $bitmap = Await-Operation $bitmapOp ([Windows.Graphics.Imaging.SoftwareBitmap])
    $result.width = [int]$decoder.PixelWidth
    $result.height = [int]$decoder.PixelHeight

    $ocrOp = $engine.RecognizeAsync($bitmap)
    $ocr = Await-Operation $ocrOp ([Windows.Media.Ocr.OcrResult])
    $lines = @($ocr.Lines | ForEach-Object { $_.Text })
    $result.text = ($lines -join "`n")
    $result.line_count = $lines.Count
    $result.ok = $true
} catch {
    $result.ok = $false
    $result.error = "$($_.Exception.GetType().Name): $($_.Exception.Message)"
}

$started.Stop()
$result.elapsed_ms = [int]$started.ElapsedMilliseconds
Write-ResultJson -Path $OutFile -Object $result
if ($result.ok) { exit 0 } else { exit 1 }
