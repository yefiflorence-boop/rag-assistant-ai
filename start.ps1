<#
.SYNOPSIS
    ONEAD Assistant RAG - lancement unifie (backend FastAPI + frontend Vite).

.DESCRIPTION
    .\start.ps1                 Demarre API (:8000) + WEB (:5173) et ouvre le navigateur.
    .\start.ps1 -NoBrowser     Idem sans ouvrir le navigateur.
    .\start.ps1 -SkipChecks    Idem sans verifier .env / node_modules / ports.

    Ctrl+C dans cette fenetre arrete proprement les deux processus.
    Equivalent sans fenetre : .\stop.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\start.ps1
#>
[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$SkipChecks,
    [switch]$Single
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root       = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir     = Join-Path $Root 'logs'
$RunDir     = Join-Path $Root '.run'
$ApiHost    = '127.0.0.1'
$ApiPort    = 8000
$WebPort    = 5173
$ApiUrl     = "http://${ApiHost}:${ApiPort}"
$WebUrl     = "http://localhost:${WebPort}"

# ---------------------------------------------------------------- helpers ---
function Write-Banner {
    Write-Host ''
    Write-Host '  ONEAD Assistant RAG - demarrage unifie' -ForegroundColor Cyan
    Write-Host '  ------------------------------------------' -ForegroundColor DarkCyan
}

function Write-Step { param([string]$Msg) Write-Host "==> $Msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Msg) Write-Host "    [OK] $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "    [!]  $Msg" -ForegroundColor Yellow }
function Write-Fail { param([string]$Msg) Write-Host "    [X]  $Msg" -ForegroundColor Red }

function Test-PortBusy {
    param([int]$Port)
    $conn = $null
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    } catch {
        $conn = $null
    }
    return [bool]$conn
}

function Get-ListenerPid {
    param([int]$Port)
    $conn = $null
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
                Select-Object -First 1
    } catch {
        $conn = $null
    }
    if ($conn) { return $conn.OwningProcess }
    return $null
}

# Lit les octets ecrits depuis la derniere lecture (tail de fichier live).
function Get-NewText {
    param([string]$Path, [ref]$State)
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    try {
        $fs = [System.IO.File]::Open(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite)
        try {
            $len = $fs.Length
            $pos = $State.Value
            if ($len -le $pos) { $State.Value = $len; return '' }
            [void]$fs.Seek($pos, [System.IO.SeekOrigin]::Begin)
            $buf = New-Object byte[] ($len - $pos)
            $read = $fs.Read($buf, 0, $buf.Length)
            $State.Value = $pos + $read
            return [System.Text.Encoding]::UTF8.GetString($buf, 0, $read)
        } finally { $fs.Dispose() }
    } catch { return '' }
}

function Write-Tagged {
    param([string]$Tag, [string]$Text, [ConsoleColor]$Color)
    if ([string]::IsNullOrWhiteSpace($Text)) { return }
    foreach ($line in ($Text -split "`r?`n")) {
        if ($line -eq '') { continue }
        Write-Host ("  {0,-4} " -f $Tag) -NoNewline
        Write-Host $line -ForegroundColor $Color
    }
}

# ------------------------------------------------------------------ setup ---
Write-Banner
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

$ApiOut   = Join-Path $LogDir 'backend.log'
$ApiErr   = Join-Path $LogDir 'backend.err.log'
$WebOut   = Join-Path $LogDir 'frontend.log'
$WebErr   = Join-Path $LogDir 'frontend.err.log'
# Note : pas de suppression des logs ici (verrouires si une instance tourne deja).
# Start-Process -RedirectStandardOutput ecrase les fichiers au demarrage.

# Python : interpreteur du venv local en priorite, sinon python du PATH.
$Python = Join-Path $Root 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = Join-Path $Root '.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $Python)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $Python = $cmd.Source } else { $Python = $null }
}

# ---------------------------------------------------------- verifications ---
Write-Step 'Verification de l''environnement'
if (-not $SkipChecks) {
    if (-not $Python) {
        Write-Fail 'Aucun interpreteur Python trouve (ni venv\Scripts\python.exe, ni .venv, ni python dans le PATH).'
        Write-Host '         Creer le venv : python -m venv venv' -ForegroundColor DarkGray
        exit 1
    }
    Write-Ok "Python : $Python"

    if (Test-Path -LiteralPath (Join-Path $Root '.env')) {
        Write-Ok '.env present'
    } else {
        Write-Warn ".env absent : reponses Azure indisponibles (copier le .env d'un autre poste)"
    }

    if (Test-Path -LiteralPath (Join-Path $Root 'frontend\node_modules')) {
        Write-Ok 'frontend/node_modules present'
    } else {
        Write-Warn 'frontend/node_modules absent : lancer "npm install" dans frontend\'
    }

    $portsToCheck = if ($Single) { @($ApiPort) } else { @($ApiPort, $WebPort) }
    foreach ($port in $portsToCheck) {
        if (Test-PortBusy -Port $port) {
            $pidOnPort = Get-ListenerPid -Port $port
            Write-Fail "Port $port deja occupe (PID $pidOnPort)."
            Write-Host "         Arreter l'instance existante : .\stop.ps1" -ForegroundColor DarkGray
            exit 1
        }
    }
    Write-Ok ("Ports {0} libres" -f ($portsToCheck -join ' et '))
}

# ------------------------------------------------------------- lancement ---
if ($Single) {
    # Mode demo : un seul processus, une seule origine (http://127.0.0.1:8000).
    # Le build doit preceder le demarrage de l'API (le montage statique est
    # decide a l'import de api.py).
    Write-Step 'Mode demo : build du frontend (npm run build)'
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npm) { $npm = Get-Command npm -ErrorAction SilentlyContinue }
    if (-not $npm) {
        Write-Fail 'npm introuvable : impossible de builder le frontend.'
        exit 1
    }
    Push-Location (Join-Path $Root 'frontend')
    try {
        & $npm.Source run build
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Fail 'Le build du frontend a echoue (voir ci-dessus).'
        exit 1
    }
    Write-Ok 'frontend/dist construit'
}

Write-Step 'Demarrage du backend (FastAPI)'
$env:PYTHONUNBUFFERED = '1'
$env:SERVE_FRONTEND = if ($Single) { '1' } else { '0' }
$apiProc = Start-Process -FilePath $Python `
    -ArgumentList @('-m', 'uvicorn', 'api:app', '--host', $ApiHost, '--port', "$ApiPort", '--reload') `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $ApiOut -RedirectStandardError $ApiErr `
    -NoNewWindow -PassThru
Write-Ok "PID $($apiProc.Id) - logs : logs\backend.log"

$webProc = $null
if (-not $Single) {
    Write-Step 'Demarrage du frontend (Vite)'
    $webProc = Start-Process -FilePath 'npm.cmd' `
        -ArgumentList @('run', 'dev', '--', '--strictPort') `
        -WorkingDirectory (Join-Path $Root 'frontend') `
        -RedirectStandardOutput $WebOut -RedirectStandardError $WebErr `
        -NoNewWindow -PassThru
    Write-Ok "PID $($webProc.Id) - logs : logs\frontend.log"
}

Set-Content -LiteralPath (Join-Path $RunDir 'api.pid') -Value $apiProc.Id
if ($webProc) { Set-Content -LiteralPath (Join-Path $RunDir 'web.pid') -Value $webProc.Id }
else { Remove-Item -LiteralPath (Join-Path $RunDir 'web.pid') -Force -ErrorAction SilentlyContinue }

# -------------------------------------------------------------- attente ----
Write-Step "Attente du backend ($ApiUrl/api/health)"
$health = $null
$deadline = (Get-Date).AddSeconds(120)
$warming = $false
while ((Get-Date) -lt $deadline) {
    if ($apiProc.HasExited) {
        Write-Fail "Le backend s'est arrete (code $($apiProc.ExitCode)). Dernieres lignes :"
        Get-Content -LiteralPath $ApiErr -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed }
        .\stop.ps1 | Out-Null
        exit 1
    }
    try {
        $health = Invoke-RestMethod -Uri "$ApiUrl/api/health" -TimeoutSec 3
        if ($health.rag_loaded) { break }
        if (-not $warming) {
            Write-Host '    ... chargement de la base RAG (ChromaDB + Azure OpenAI)' -ForegroundColor DarkGray
            $warming = $true
        }
    } catch { }
    Start-Sleep -Milliseconds 700
}

if (-not $health) {
    Write-Fail 'Le backend ne repond pas sur /api/health apres 120 s.'
    Write-Host '         Voir logs\backend.err.log puis .\stop.ps1' -ForegroundColor DarkGray
    .\stop.ps1 | Out-Null
    exit 1
}
if ($health.rag_loaded) {
    Write-Ok 'health : status=ok rag_loaded=true (base prechargee)'
} else {
    Write-Warn 'health : status=ok mais rag_loaded=false (warmup en cours, voir logs\backend.err.log)'
}

if (-not $Single) {
    Write-Step 'Attente du frontend (Vite)'
    $webDeadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $webDeadline) {
        if ($webProc.HasExited) {
            Write-Fail "Vite s'est arrete. Dernieres lignes :"
            Get-Content -LiteralPath $WebErr -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed }
            .\stop.ps1 | Out-Null
            exit 1
        }
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:${WebPort}" -TimeoutSec 3 -UseBasicParsing
            break
        } catch { Start-Sleep -Milliseconds 700 }
    }
}

# --------------------------------------------------------------- resultat --
$InterfaceUrl = if ($Single) { $ApiUrl } else { $WebUrl }
Write-Host ''
Write-Host '  ------------------------------------------' -ForegroundColor DarkCyan
Write-Host '  Interface   : ' -NoNewline -ForegroundColor White
Write-Host $InterfaceUrl -ForegroundColor Green
Write-Host '  API         : ' -NoNewline -ForegroundColor White
Write-Host "$ApiUrl/api/health" -ForegroundColor Green
if ($Single) {
    Write-Host '  Mode        : ' -NoNewline -ForegroundColor White
    Write-Host 'demo (1 processus, 1 origine, build statique)' -ForegroundColor Green
} else {
    Write-Host '  Mode        : ' -NoNewline -ForegroundColor White
    Write-Host 'dev (Vite :5173 + proxy vers :8000, HMR actif)' -ForegroundColor Green
}
Write-Host '  Base RAG    : ' -NoNewline -ForegroundColor White
Write-Host 'data\chroma_db (reindexer si data\raw change)' -ForegroundColor DarkGray
Write-Host '  Logs        : ' -NoNewline -ForegroundColor White
Write-Host 'logs\backend.log | logs\frontend.log' -ForegroundColor DarkGray
Write-Host '  ------------------------------------------' -ForegroundColor DarkCyan

if (-not $NoBrowser) {
    Start-Process $InterfaceUrl
    Write-Host '  Navigateur ouvert.' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '  Ctrl+C = arreter les deux processus.' -ForegroundColor Yellow
Write-Host ''

function Get-FileLength {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        return (Get-Item -LiteralPath $Path).Length
    }
    return 0
}

# ------------------------------------------------------- logs temps reel ---
# On demarre a la fin de chaque fichier : seuls les NOUVEAUX logs sont affiches.
$apiOutState = Get-FileLength $ApiOut
$apiErrState = Get-FileLength $ApiErr
$webOutState = Get-FileLength $WebOut
$webErrState = Get-FileLength $WebErr

try {
    while ($true) {
        Write-Tagged -Tag 'API' -Text (Get-NewText -Path $ApiOut -State ([ref]$apiOutState)) -Color Cyan
        Write-Tagged -Tag 'API' -Text (Get-NewText -Path $ApiErr -State ([ref]$apiErrState)) -Color DarkCyan
        Write-Tagged -Tag 'WEB' -Text (Get-NewText -Path $WebOut -State ([ref]$webOutState)) -Color Green
        Write-Tagged -Tag 'WEB' -Text (Get-NewText -Path $WebErr -State ([ref]$webErrState)) -Color DarkGreen

        if ($apiProc.HasExited -and (-not $webProc -or $webProc.HasExited)) { break }
        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host ''
    Write-Step 'Arret des processus...'
    & (Join-Path $Root 'stop.ps1') | Out-Null
    Write-Host '  Arret termine.' -ForegroundColor Green
}
