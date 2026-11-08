# One-time setup for Reel Studio on Windows.
# Right-click -> "Run with PowerShell", or ask Claude: "run setup.ps1".
# Installs (if missing) ffmpeg, Node.js, Git and Python 3.12 with winget, accepting their standard install terms,
# then the project's own pieces and the speech-to-text model (~250 MB). Safe to run again.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') }
function Need($cmd, $id) {
    if (Have $cmd) { Write-Host "ok   $cmd"; return }
    Write-Host "installing $id ..."
    winget install --id $id -e --silent --accept-source-agreements --accept-package-agreements
    Refresh-Path
    if (-not (Have $cmd)) { throw "$cmd still not found after installing $id. Restart the computer and run setup again." }
}
function Check($what) { if ($LASTEXITCODE) { throw "$what failed (exit $LASTEXITCODE)" } }

# rendering breaks on Windows when the project sits deep in folders (260-character path limit)
if ($PSScriptRoot.Length -gt 80) {
    Write-Warning "This folder's path is $($PSScriptRoot.Length) characters long. Rendering can fail on long paths: move the project to a short folder like C:\Users\$env:USERNAME\reel-studio."
}

if (-not (Have 'winget')) { throw 'winget is missing: install "App Installer" from the Microsoft Store, then run setup again.' }
Need 'ffmpeg' 'Gyan.FFmpeg'
Need 'node' 'OpenJS.NodeJS.LTS'
Need 'git' 'Git.Git'
$py312 = $false
if (Have 'py') { try { $py312 = ((& py -3.12 -c "print(1)" 2>$null) -eq '1') } catch {} }  # py errors on stderr when 3.12 is missing
if ($py312) { Write-Host 'ok   python 3.12' } else {
    winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
    Refresh-Path
}

Write-Host 'installing the video editor (Remotion) ...'
npm.cmd install --no-audit --no-fund; Check 'npm install'
npx.cmd remotion browser ensure; Check 'downloading the render browser'

Write-Host 'installing speech-to-text ...'
py -3.12 -m pip install --quiet faster-whisper numpy; Check 'pip install'
py -3.12 -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8'); print('ok   speech model')"; Check 'speech model download'
py -3.12 tools/test_pace.py; Check 'self-check'

Write-Host ''
if (Test-Path brand.json) { Write-Host 'Setup done.' } else {
    Write-Host 'Setup done. Next: open this folder in Claude Code and say "set me up".'
}
