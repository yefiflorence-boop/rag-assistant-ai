<#
.SYNOPSIS
    ONEAD Assistant RAG - arret du backend (FastAPI) et du frontend (Vite).

.DESCRIPTION
    .\stop.ps1        Arrete les processus lances par .\start.ps1 (PIDs dans .run\).
    .\stop.ps1 -Quiet N'affiche rien (utile dans un script).

    Les processus sont recherches par PID (.run\) puis par port (8000 / 5173).
    Pour chaque port on tue l'ARBRE complet (enfants d'abord, parent ensuite) :
    avec `uvicorn --reload`, l'enfant herite du socket d'ecoute et survit au
    parent, ce qui laisserait le port occupe apres un arret.
#>
[CmdletBinding()]
param(
    [switch]$Quiet
)

$ErrorActionPreference = 'SilentlyContinue'
Set-StrictMode -Version Latest

$Root   = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunDir = Join-Path $Root '.run'
$Ports  = @(8000, 5173)

if (-not $Quiet) {
    Write-Host ''
    Write-Host '  Arret de ONEAD Assistant RAG...' -ForegroundColor Cyan
}

function Write-Kill {
    param([string]$Msg)
    if (-not $Quiet) { Write-Host "    [OK] $Msg" -ForegroundColor Green }
}

function Write-Warn {
    param([string]$Msg)
    if (-not $Quiet) { Write-Host "    [!]  $Msg" -ForegroundColor Yellow }
}

function Get-ListeningPid {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    } catch {
        $conn = $null
    }
    if ($conn) { return [int]($conn | Select-Object -First 1).OwningProcess }
    return 0
}

# Liste des descendants d'un processus (enfants, petits-enfants, ...).
function Get-ProcessTree {
    param([int]$RootPid)
    $ids = New-Object System.Collections.Generic.List[int]
    if ($RootPid -le 0) { return $ids }
    $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    $queue = New-Object System.Collections.Generic.Queue[int]
    $queue.Enqueue($RootPid)
    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        if ($ids.Contains($current)) { continue }
        $ids.Add($current)
        foreach ($child in $all) {
            if ([int]$child.ParentProcessId -eq $current) {
                $queue.Enqueue([int]$child.ProcessId)
            }
        }
    }
    return $ids
}

# Tue l'arbre complet : descendants d'abord (detenteurs du socket herite),
# puis la racine, puis un taskkill /T de secours.
function Stop-Tree {
    param([int]$RootPid)
    if ($RootPid -le 0) { return }
    $tree = Get-ProcessTree -RootPid $RootPid
    $ordered = @($tree | Sort-Object -Descending)
    foreach ($id in $ordered) {
        if ($id -eq $RootPid) { continue }
        Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
    }
    Stop-Process -Id $RootPid -Force -ErrorAction SilentlyContinue
    & taskkill /PID $RootPid /T /F 2>&1 | Out-Null
}

# --- 1. PIDs enregistres par start.ps1 -------------------------------------
foreach ($name in @('api.pid', 'web.pid')) {
    $pidFile = Join-Path $RunDir $name
    if (Test-Path -LiteralPath $pidFile) {
        $procId = 0
        $raw = (Get-Content -LiteralPath $pidFile -Raw)
        if ($raw -match '(\d+)') { $procId = [int]$Matches[1] }
        if ($procId -gt 0) {
            Stop-Tree -RootPid $procId
            Write-Kill "processus $name (PID $procId) arrete"
        }
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    }
}

# --- 2. Ecouteurs sur les ports du projet ----------------------------------
foreach ($port in $Ports) {
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $owner = Get-ListeningPid -Port $port
        if ($owner -le 0) { break }
        Stop-Tree -RootPid $owner
        Start-Sleep -Milliseconds 600
    }
    if ((Get-ListeningPid -Port $port) -gt 0) {
        Write-Warn "port $port toujours occupe (verifier manuellement)"
    } else {
        Write-Kill "port $port libere"
    }
}

if (-not $Quiet) {
    Write-Host '  Tout est arrete.' -ForegroundColor Green
    Write-Host ''
}
