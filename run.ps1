<#
  Relay MCP - dev runner (Windows / PowerShell)

  Usage:
    .\run.ps1 install        Install the relay-mcp package in editable mode
    .\run.ps1 register       Add relay to ~/.claude/claude_code_config.json
    .\run.ps1 test [DIR]     Run the audit engine directly on DIR (default: current dir)
    .\run.ps1 serve          Start the MCP server in the foreground (stdio; for debugging)
    .\run.ps1 all            install + register

  Env:
    RELAY_API_KEY   API key used for register/test/serve (optional for local test)
#>

param(
    [Parameter(Position = 0)] [string] $Cmd = "help",
    [Parameter(Position = 1)] [string] $Dir = "."
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$ConfigPath = Join-Path $env:USERPROFILE ".claude\claude_code_config.json"

function Install-Pkg {
    Write-Host "==> pip install -e ." -ForegroundColor Cyan
    Push-Location $Root
    try { python -m pip install -e . } finally { Pop-Location }
}

function Register-Mcp {
    Write-Host "==> Registering 'relay' in $ConfigPath" -ForegroundColor Cyan
    $dir = Split-Path $ConfigPath
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

    if (Test-Path $ConfigPath) {
        $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    } else {
        $cfg = [PSCustomObject]@{}
    }
    if (-not $cfg.PSObject.Properties.Name -contains "mcpServers") {
        $cfg | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([PSCustomObject]@{}) -Force
    }
    if ($null -eq $cfg.mcpServers) {
        $cfg | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([PSCustomObject]@{}) -Force
    }

    $key = if ($env:RELAY_API_KEY) { $env:RELAY_API_KEY } else { "your_key_here" }
    $entry = [PSCustomObject]@{
        command = "relay-mcp"
        env     = [PSCustomObject]@{ RELAY_API_KEY = $key }
    }
    $cfg.mcpServers | Add-Member -NotePropertyName relay -NotePropertyValue $entry -Force

    $cfg | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigPath -Encoding utf8
    Write-Host "Done. Restart Claude Code, then say: 'Audit this codebase for latency issues'" -ForegroundColor Green
    if ($key -eq "your_key_here") {
        Write-Host "NOTE: set RELAY_API_KEY and re-run, or edit the key in $ConfigPath" -ForegroundColor Yellow
    }
}

function Test-Audit {
    param([string] $Target)
    $abs = (Resolve-Path $Target).Path
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $name = Split-Path $abs -Leaf
    $out = Join-Path $Root "relay-report-$name-$stamp.json"
    Write-Host "==> Running audit engine on: $abs" -ForegroundColor Cyan
    Push-Location $Root
    try {
        python -c "from mcp_server.engine.engine import AuditEngine; import json; r = AuditEngine().run_on_codebase(r'$abs'); open(r'$out','w',encoding='utf-8').write(json.dumps(r.to_dict(), indent=2, default=str))"
    } finally { Pop-Location }
    Write-Host "==> Wrote results to: $out" -ForegroundColor Green
}

function Serve {
    Write-Host "==> Starting MCP server (stdio). Ctrl+C to stop." -ForegroundColor Cyan
    Push-Location $Root
    try { python -m mcp_server.server } finally { Pop-Location }
}

switch ($Cmd.ToLower()) {
    "install"  { Install-Pkg }
    "register" { Register-Mcp }
    "test"     { Test-Audit -Target $Dir }
    "serve"    { Serve }
    "all"      { Install-Pkg; Register-Mcp }
    default {
        Write-Host "Relay MCP dev runner" -ForegroundColor Cyan
        Write-Host "  .\run.ps1 install      Install package (pip install -e .)"
        Write-Host "  .\run.ps1 register     Add to Claude Code config"
        Write-Host "  .\run.ps1 all          install + register"
        Write-Host "  .\run.ps1 test [DIR]   Audit a directory directly (no MCP)"
        Write-Host "  .\run.ps1 serve        Run MCP server in foreground (debug)"
    }
}
