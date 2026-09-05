#!/usr/bin/env bash
cd "$(dirname "$0")"

if command -v pnpm >/dev/null 2>&1; then
    pnpm dev
elif command -v npm >/dev/null 2>&1; then
    npm run dev
elif command -v bun >/dev/null 2>&1; then
    bun run dev
else
    echo "No package manager (pnpm/npm/bun) found in PATH. Please install pnpm or nodejs."
    exit 1
fi
