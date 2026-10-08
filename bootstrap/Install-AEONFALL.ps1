param(
    [string]$ProjectFile,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$PackageRoot = Split-Path -Parent $PSScriptRoot
if (-not $ProjectFile) {
    Add-Type -AssemblyName System.Windows.Forms
    $Picker = New-Object System.Windows.Forms.OpenFileDialog
    $Picker.Filter = 'UEFN project (*.uefnproject)|*.uefnproject'
    $Picker.Title = 'Select the Blank AEONFALL project created in UEFN'
    if ($Picker.ShowDialog() -ne 'OK') { exit 0 }
    $ProjectFile = $Picker.FileName
}
$Installer = Join-Path $PackageRoot 'tools/install_uefn_sources.py'
$InstallArgs = @($Installer, $ProjectFile)
if ($DryRun) { $InstallArgs += '--dry-run' }
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 @InstallArgs
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python @InstallArgs
} else {
    throw 'Install Python 3.10 or newer for Windows, then rerun this launcher.'
}
if ($LASTEXITCODE -ne 0) { throw 'AEONFALL installation failed; read the error above.' }
if ($DryRun) {
    Write-Host 'Dry run complete. Run again without -DryRun to install sources.'
} else {
    Write-Host 'Source installation complete. Run the editor assembly script in UEFN; see docs/UEFN_STARTER.md.'
}
