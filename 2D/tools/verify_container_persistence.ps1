param([Parameter(Mandatory=$true)][string]$RunName)
$ErrorActionPreference = 'Stop'
$experimentRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $experimentRoot
if ($RunName -notmatch '^[A-Za-z0-9_-]+$') { throw 'RunName must be a directory name, not a path.' }
$resultDir = Join-Path $experimentRoot "runs\container_validation\$RunName"
$linuxRun = "/workspaces/NR-material-state/2D/runs/container_validation/$RunName"
$mount = "type=bind,source=$projectRoot,target=/workspaces/NR-material-state"
$containerName = 'nr-persistence-' + [guid]::NewGuid().ToString('N').Substring(0,12)
docker run --rm --name $containerName --mount $mount nr-spatial-2d:py311 python tools/container_persistence.py write $linuxRun
if ($LASTEXITCODE -ne 0) { throw 'First persistence container failed.' }
# --rm must have removed the first container before the second one can use its name.
$remaining = docker ps -a --filter "name=^/$containerName`$" --format '{{.Names}}'
if ($remaining) { throw 'The first container was not removed.' }
$watch = [System.Diagnostics.Stopwatch]::StartNew()
docker build --progress=plain -t nr-spatial-2d:py311 (Join-Path $experimentRoot "environment") *> (Join-Path $resultDir 'cached-rebuild.log')
if ($LASTEXITCODE -ne 0) { throw 'Cached rebuild failed.' }
$watch.Stop()
docker run --rm --name $containerName --mount $mount nr-spatial-2d:py311 python tools/container_persistence.py verify $linuxRun
if ($LASTEXITCODE -ne 0) { throw 'Second persistence container failed.' }
[pscustomobject]@{
    status='passed'; first_container_removed=$true; image_rebuilt=$true;
    cached_rebuild_seconds=$watch.Elapsed.TotalSeconds; host_directory=$resultDir;
    second_container_verified_all_recorded_hashes=$true
} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $resultDir 'persistence.json')
Write-Output 'Bind-mounted artifacts survived container removal and image rebuild.'
