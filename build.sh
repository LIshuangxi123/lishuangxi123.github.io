#!/usr/bin/env bash
# 重建源索引。macOS / Linux / GitHub Actions 都用这个。
set -euo pipefail
cd "$(dirname "$0")"

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
    echo "找不到 python3，请先安装（macOS 上可以 brew install python3）" >&2
    exit 1
fi

exec "$PY" tools/mkindex.py "$@"
