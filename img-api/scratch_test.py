import subprocess
import sys
import psutil

print("1. Running Get-Counter command with semicolon separator...")
cmd = [
    "powershell", "-NoProfile", "-Command",
    '(Get-Counter -Counter "\\GPU Process Memory(*)\\Local Usage" -ErrorAction SilentlyContinue).CounterSamples | Where-Object { $_.CookedValue -gt 0 } | ForEach-Object { $pidVal = 0; if ($_.InstanceName -match "pid_(\\d+)") { $pidVal = [int]$Matches[1] }; Write-Output ("{0};{1}" -f $pidVal, ($_.CookedValue / 1MB)) }'
]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
print("Return code:", res.returncode)
print("Raw stdout lines:")
for line in res.stdout.strip().splitlines():
    print(repr(line))

print("\n2. Parsing and categorizing...")
pid_map = {}
for line in res.stdout.strip().splitlines():
    parts = line.split(";")
    if len(parts) == 2:
        try:
            pid = int(parts[0])
            mem_mb = float(parts[1].replace(",", "."))
            if pid > 0:
                pid_map[pid] = pid_map.get(pid, 0.0) + mem_mb
        except ValueError as e:
            print("ValueError for line:", repr(line), "error:", e)

print("PID Map:", pid_map)

breakdown = {"stable_diffusion": 0.0, "lm_studio": 0.0, "system": 0.0}
for pid, mem_mb in pid_map.items():
    proc_name = ""
    try:
        proc_name = psutil.Process(pid).name().lower()
    except Exception as e:
        proc_name = f"<error: {e}>"
    print(f"PID {pid}: name = {proc_name}, mem = {mem_mb} MB")
    
    # Categorize
    if any(k in proc_name for k in ("python", "forge", "stable", "webui", "sd")):
        breakdown["stable_diffusion"] += mem_mb
    elif any(k in proc_name for k in ("lms", "lm studio", "lmstudio")):
        breakdown["lm_studio"] += mem_mb
    else:
        breakdown["system"] += mem_mb

print("Final Breakdown:", breakdown)
