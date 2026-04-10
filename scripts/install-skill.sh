#!/usr/bin/env bash
# Install the memsync Claude Code skill into ~/.claude/skills/memsync/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/claude-skill/.claude/skills/memsync"
TARGET_DIR="${HOME}/.claude/skills/memsync"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "ERROR: source skill directory not found: ${SOURCE_DIR}" >&2
  exit 1
fi

mkdir -p "${TARGET_DIR}"
cp -R "${SOURCE_DIR}/." "${TARGET_DIR}/"
echo "installed memsync skill to ${TARGET_DIR}"
echo "restart Claude Code, then check /skills for 'memsync'"
