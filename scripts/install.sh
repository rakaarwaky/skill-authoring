#!/usr/bin/env bash
# skills/skill-authoring/tools/scripts/install.sh
#
# Installer for the Skill Authoring pack (skill-authoring-cli + skill-authoring-mcp).
#
# Installs uv-managed Python venv at <repo>/.venv and two launcher
# scripts into the XDG bin home ($XDG_BIN_HOME, default $HOME/.local/bin):
#   - skill-authoring-cli: runs `modules/root_cli_entry.py`
#   - skill-authoring-mcp: runs `modules/root_mcp_entry.py` (MCP stdio server)
#
# Non-interactive, idempotent, no sudo required unless --global is passed.
# By default it also registers the pack as an MCP server in ~/.grok/config.toml
# so Grok Build can call skill-authoring-cli verbs through stdio.
#
# Usage:
#   bash scripts/install.sh             # local XDG install (default)
#   bash scripts/install.sh --global    # system-wide install (/usr/local/bin, sudo)
#   bash scripts/install.sh --check     # dry-run: verify prerequisites only
#   bash scripts/install.sh --no-mcp    # skip ~/.grok/config.toml MCP registration
#   bash scripts/install.sh --help      # show usage
set -euo pipefail

# --- Resolve paths (this file lives at <repo>/skills/skill-authoring/tools/scripts/) ---
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
TOOLS_DIR="$(cd -P "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd)"
SKILL_AUTHORING_DIR="$(cd -P "$TOOLS_DIR/.." >/dev/null 2>&1 && pwd)"
REPO_ROOT="$SKILL_AUTHORING_DIR"
VENV_DIR="$TOOLS_DIR/.venv"

BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
MODE="local"
CHECK_ONLY=false
INSTALL_MCP=true
MCP_ARG=""
if ! $INSTALL_MCP; then MCP_ARG="--no-mcp"; fi

info()  { printf "[INFO]  %s\n" "$*"; }
ok()    { printf "[ OK ]  %s\n" "$*"; }
warn()  { printf "[WARN]  %s\n" "$*" >&2; }
err()   { printf "[FAIL]  %s\n" "$*" >&2; }
step()  { printf "\n>>> %s\n" "$*"; }
die()   { err "$@"; exit 1; }

usage() {
  cat <<EOF
Usage: bash scripts/install.sh [options]

Installer for the Skill Authoring pack (skill-authoring-cli + skill-authoring-mcp).

Options:
  --local     Local XDG install at \$XDG_BIN_HOME (default \$HOME/.local/bin)
  --global    System-wide install at /usr/local/bin (requires root/sudo)
  --check     Dry-run: verify prerequisites only, no changes
  --no-mcp    Skip writing the MCP server entry to ~/.grok/config.toml
  -h, --help  Show this help

Examples:
  bash scripts/install.sh            # local XDG install + MCP registration
  bash scripts/install.sh --global   # system-wide install
  bash scripts/install.sh --no-mcp   # local install without MCP registration
  bash scripts/install.sh --check    # verify prerequisites only
EOF
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    --local) MODE="local" ;;
    --global) MODE="global" ;;
    --check) CHECK_ONLY=true ;;
    --no-mcp) INSTALL_MCP=false ;;
    -h|--help) usage ;;
    *) die "Unknown option: $arg (use -h for help)" ;;
  esac
done

# --- Prerequisites ---
if ! command -v python3 &>/dev/null; then
  die "python3 is required but not on PATH. Install Python >= 3.10 first."
fi
if ! command -v uv &>/dev/null; then
  warn "uv is not on PATH. Installing uv via the official installer..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv &>/dev/null || die "uv is required but could not be installed. Install manually: https://docs.astral.sh/uv/getting-started/installation/"

PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="${PYVER%%.*}"
PY_MINOR="${PYVER#*.}"
if (( PY_MAJOR < 3 )) || (( PY_MAJOR == 3 && PY_MINOR < 10 )); then
  die "Python $PYVER is too old; Skill Authoring requires Python >= 3.10."
fi
ok "Python $PYVER"
ok "uv: $(uv --version)"

if $CHECK_ONLY; then
  step "Prerequisite check complete"
  ok "python3 $PYVER (>= 3.10)"
  ok "uv $(uv --version)"
  ok "tools tree: $TOOLS_DIR"
  exit 0
fi

# --- Create uv-managed venv ---
step "Creating Python venv (uv)"
if [[ -d "$VENV_DIR" ]] && [[ -f "$VENV_DIR/bin/activate" ]]; then
  ok "venv already exists: $VENV_DIR"
else
  uv venv "$VENV_DIR" && ok "Created venv: $VENV_DIR" || die "Failed to create venv at $VENV_DIR"
fi

# Sync the project's uv-managed dependencies if a uv.lock/pyproject exists.
if [[ -f "$TOOLS_DIR/pyproject.toml" ]] || [[ -f "$TOOLS_DIR/uv.lock" ]]; then
  step "Syncing uv dependencies"
  uv sync --venv "$VENV_DIR" && ok "uv sync complete" || warn "uv sync completed with warnings (non-fatal)"
else
  info "No pyproject.toml/uv.lock in tools tree; skipping uv sync."
fi

# --- Install skill-authoring-cli launcher ---
step "Installing skill-authoring-cli launcher"
if [[ "$MODE" == "global" ]]; then
  if [[ "$(id -u)" -ne 0 ]]; then
    warn "Global install requires root; re-running with sudo..."
    sudo bash "$SCRIPT_DIR/install.sh" --global ${CHECK_ONLY:+--check} ${MCP_ARG:+$MCP_ARG}
    exit $?
  fi
  BIN_DIR="/usr/local/bin"
fi

mkdir -p "$BIN_DIR"

# Bake the absolute tools path into the launcher (repo convention: install.sh
# writes TOOLS_DIR="$TOOLS_DIR" into its launcher). A relative walk from
# $BIN_DIR cannot reliably reach the repo checkout, so the path is fixed at
# install time. Every package exposes its public API under a sibling `src/`
# directory with bare sibling imports (e.g. design/src imports
# capabilities_skills_* directly), so every modules/*/src must be on
# PYTHONPATH, not just modules itself.
SRC_DIRS=""
for d in "$TOOLS_DIR"/modules/*/src; do
  [[ -d "$d" ]] && SRC_DIRS="$SRC_DIRS:$d"
done

# CLI launcher: skill-authoring-cli
CLI_LAUNCHER="$BIN_DIR/skill-authoring-cli"
rm -f "$CLI_LAUNCHER"
cat > "$CLI_LAUNCHER" <<CLI_EOF
#!/usr/bin/env bash
set -euo pipefail
# skill-authoring-cli launcher for the Skill Authoring pack.
TOOLS_DIR="$TOOLS_DIR"
VENV_DIR="\$TOOLS_DIR/.venv"
[[ -f "\$VENV_DIR/bin/activate" ]] && source "\$VENV_DIR/bin/activate"
export PYTHONPATH="\$TOOLS_DIR/modules${SRC_DIRS}\${PYTHONPATH:+:\${PYTHONPATH}}"
exec python3 "\$TOOLS_DIR/modules/root_cli_entry.py" "\$@"
CLI_EOF
chmod 755 "$CLI_LAUNCHER"
ok "skill-authoring-cli launcher: $CLI_LAUNCHER"

# MCP launcher: skill-authoring-mcp
# Deliberately does NOT put $TOOLS_DIR/modules on PYTHONPATH: that would make
# `import mcp` resolve to the feature dir (modules/mcp) instead of the
# installed mcp library. root_mcp_entry.py imports mcp.server at its top,
# then adds modules/ to sys.path after that — the entry owns the ordering.
MCP_LAUNCHER="$BIN_DIR/skill-authoring-mcp"
rm -f "$MCP_LAUNCHER"
cat > "$MCP_LAUNCHER" <<MCP_EOF
#!/usr/bin/env bash
set -euo pipefail
# skill-authoring-mcp launcher for the Skill Authoring pack.
TOOLS_DIR="$TOOLS_DIR"
VENV_DIR="\$TOOLS_DIR/.venv"
[[ -f "\$VENV_DIR/bin/activate" ]] && source "\$VENV_DIR/bin/activate"
export PYTHONPATH="\${PYTHONPATH:+\${PYTHONPATH}:}${SRC_DIRS:1}"
exec python3 "\$TOOLS_DIR/modules/root_mcp_entry.py" "\$@"
MCP_EOF
chmod 755 "$MCP_LAUNCHER"
ok "skill-authoring-mcp launcher: $MCP_LAUNCHER"

# Short aliases: sac -> skill-authoring-cli, sam -> skill-authoring-mcp.
SAC_ALIAS="$BIN_DIR/sac"
SAM_ALIAS="$BIN_DIR/sam"
rm -f "$SAC_ALIAS" "$SAM_ALIAS"
ln -sf skill-authoring-cli "$SAC_ALIAS"
ln -sf skill-authoring-mcp "$SAM_ALIAS"
ok "aliases: sac -> skill-authoring-cli, sam -> skill-authoring-mcp ($BIN_DIR)"

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  warn "$BIN_DIR is not on your PATH — add it (e.g. export PATH=\"$BIN_DIR:\$PATH\") then run: sac lint"
fi

# --- Register pack as an MCP server in ~/.grok/config.toml ---
if $INSTALL_MCP; then
  step "Registering skill-authoring-tools MCP server"
  GROK_CONFIG="$HOME/.grok/config.toml"
  if [[ ! -f "$GROK_CONFIG" ]]; then
    warn "$GROK_CONFIG not found — skipping MCP registration"
  elif grep -q '^\[mcp_servers.skill-authoring-tools\]' "$GROK_CONFIG"; then
    ok "MCP server entry already present in $GROK_CONFIG"
  else
    {
      echo ""
      echo "[mcp_servers.skill-authoring-tools]"
      echo "command = \"skill-authoring-mcp\""
      echo "args = []"
    } >> "$GROK_CONFIG"
    ok "MCP server entry added to $GROK_CONFIG"
  fi
fi

step "Installation complete"
ok "Run: skill-authoring-cli lint        (inspect the skill tree)"
ok "Run: skill-authoring-cli list        (list all skills)"
ok "Run: skill-authoring-cli read <name> (read a skill's SKILL.md)"
ok "Run: skill-authoring-cli --help      (see all commands)"
echo
echo "Repo root:  $REPO_ROOT"
echo "Tools tree: $TOOLS_DIR"
echo "Venv:       $VENV_DIR"
echo "Bin dir:    $BIN_DIR"
if $INSTALL_MCP; then
  echo "MCP config: $GROK_CONFIG (skill-authoring-tools)"
fi
