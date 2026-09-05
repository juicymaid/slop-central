#!/usr/bin/env bash
cd "$(dirname "$0")"

PORT="${PORT:-8000}"

# If port is already occupied, free it before starting
if fuser "${PORT}/tcp" >/dev/null 2>&1; then
    echo "[!] Port ${PORT} is already in use."
    echo "[*] Terminating existing process on port ${PORT}..."
    fuser -k -9 "${PORT}/tcp" >/dev/null 2>&1
    sleep 1
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
    exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT}" --reload --reload-exclude ./files/
elif command -v uv >/dev/null 2>&1; then
    exec uv run uvicorn main:app --host 0.0.0.0 --port "${PORT}" --reload --reload-exclude ./files/
else
    exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT}" --reload --reload-exclude ./files/
fi
