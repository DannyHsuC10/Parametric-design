param([string]$SdkRoot)

$ErrorActionPreference = 'Stop'
$target = Join-Path $PSScriptRoot 'build/webview2'
$csc = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
if ($SdkRoot) {
    $core = Join-Path $SdkRoot 'lib/net462/Microsoft.Web.WebView2.Core.dll'
    $loader = Join-Path $SdkRoot 'runtimes/win-x64/native/WebView2Loader.dll'
} else {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
    $vs = if (Test-Path -LiteralPath $vswhere) {
        & $vswhere -latest -products '*' -property installationPath | Select-Object -First 1
    }
    if (-not $vs) { throw 'Provide -SdkRoot pointing to an extracted Microsoft.Web.WebView2 SDK.' }
    $private = Join-Path $vs 'Common7/IDE/PrivateAssemblies'
    $core = Join-Path $private 'Microsoft.Web.WebView2.Core.dll'
    $loader = Join-Path $private 'WebView2Loader.dll'
}
foreach ($file in @($core, $loader, $csc)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing dependency: $file" }
}
New-Item -ItemType Directory -Path $target -Force | Out-Null
$source = Join-Path $PSScriptRoot 'webview2/ReportHost.cs'
& $csc /nologo /platform:x64 /target:exe "/out:$target/ReportHost.exe" "/reference:$core" /reference:System.Drawing.dll /reference:System.Windows.Forms.dll $source
if ($LASTEXITCODE) { throw "WebView2 host compilation failed ($LASTEXITCODE)." }
Copy-Item -LiteralPath $core, $loader -Destination $target -Force
