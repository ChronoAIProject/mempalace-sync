# 4060 Setup Runbook — mempalace-sync v0.2 host mode + NyxID

End-to-end runbook for standing up the always-on host on the Linux + 4060 box. Read top to bottom; do not skip steps. If a step's verification fails, fix before moving on.

**Owner:** Lexa
**Date:** drafted 2026-04-11
**Predecessor:** Mac built and tested the host_server.py REST shim (`mempalace-sync host serve` works locally end-to-end). This runbook moves the same shim onto the 4060 and puts NyxID in front of it so remote AI agents can reach it.

---

## What we are trying to prove

A remote MCP client (Claude Code on the Mac, or anywhere else on the internet) can call a `mempalace_*` tool, and the tool actually executes against the palace data living on the 4060 — without exposing any raw API keys, without port-forwarding, and with per-agent token isolation handled by NyxID.

```
Mac Claude Code  →  NyxID Cloud Gateway  →  nyxid node (on 4060)
                                                 ↓
                                          mempalace-sync host server (FastAPI, :8765)
                                                 ↓
                                          import mempalace → ChromaDB on disk
```

If at the end of this runbook a curl from the Mac (going through NyxID) returns a real palace_status JSON populated by the 4060, we are done with v0.2 alpha.

---

## Prerequisites — verify before starting

```bash
# 4060 box, terminal
uname -a                    # expect: Linux ... x86_64
nvidia-smi                  # expect: 4060 visible (we don't need GPU for the shim, but verifies the box is the right one)
docker --version            # expect: Docker version 24+ — install if missing: https://docs.docker.com/engine/install/
docker compose version      # expect: Docker Compose version v2.x
git --version
python3 --version           # expect: 3.11 or 3.12 (mempalace requires 3.9+, but stick with 3.11+)
curl --version
openssl version
```

If Docker is not installed, install Docker Engine (not Desktop) on Linux per the official docs and add yourself to the `docker` group: `sudo usermod -aG docker $USER && newgrp docker`. Verify with `docker run hello-world`.

**Network notes:** know the 4060's LAN IP (`ip addr show`) and whether it has any kind of public reachability. NyxID `nyxid node` only needs **outbound** WebSocket — no inbound port forwarding required. So even if the 4060 is behind a residential NAT, this should work as long as outbound 443 is open.

---

## Step 1 — Clone both repos

```bash
mkdir -p ~/code && cd ~/code
git clone https://github.com/ChronoAIProject/mempalace-sync.git
git clone https://github.com/ChronoAIProject/NyxID.git
```

Verify both clones exist and are on `main`:

```bash
cd ~/code/mempalace-sync && git status && git log --oneline -3
cd ~/code/NyxID && git status && git log --oneline -3
```

---

## Step 2 — Install mempalace-sync host mode and bring up the shim

```bash
cd ~/code/mempalace-sync
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[host]   # pulls fastapi + uvicorn + mempalace + chromadb
```

Pick where the palace lives on the 4060. Recommendation: `/var/lib/mempalace` or `~/mempalace-data` — somewhere with plenty of disk and that you back up.

```bash
export MEMPALACE_PALACE=$HOME/mempalace-data
mkdir -p "$MEMPALACE_PALACE"
```

Smoke test the shim **without** NyxID first, just to confirm it imports mempalace correctly on Linux + Python 3.11/3.12:

```bash
mempalace-sync host serve --host 127.0.0.1 --port 8765 &
SHIM_PID=$!
sleep 3
curl -s http://127.0.0.1:8765/                                  # expect: service identifier JSON
curl -s -X POST http://127.0.0.1:8765/v1/tools/mempalace_status # expect: {ok: true, palace_path: ".../mempalace-data", result: {...}}
kill $SHIM_PID
```

**If this fails** (import error, chromadb wheel mismatch on Linux, etc.) → **stop here, file an issue against mempalace-sync, do not move on.** We need the shim working before NyxID can do anything useful.

---

## Step 3 — Make the shim run as a service (systemd user unit)

The shim needs to stay running across reboots. Create a user-level systemd unit so you don't need root and don't need to restart it after every login.

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/mempalace-sync-host.service <<'EOF'
[Unit]
Description=mempalace-sync host server (FastAPI shim around MemPalace)
After=network-online.target

[Service]
Type=simple
Environment=MEMPALACE_PALACE=%h/mempalace-data
ExecStart=%h/code/mempalace-sync/.venv/bin/mempalace-sync host serve --host 127.0.0.1 --port 8765
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now mempalace-sync-host.service
systemctl --user status mempalace-sync-host.service   # expect: active (running)
loginctl enable-linger $USER                          # so the user service runs even when logged out
```

Verify it survived activation:

```bash
curl -s http://127.0.0.1:8765/v1/tools/mempalace_status
```

If you get JSON, the host shim is now permanent on the 4060.

---

## Step 4 — Stand up NyxID self-host

Follow the official quick start (the README has a one-paste bash block). Summarized here so this runbook is self-contained:

```bash
cd ~/code/NyxID

# Generate dev env + RSA keys (the README's Step 2 block)
EK=$(openssl rand -hex 32)
cat > .env.dev <<EOF
MONGO_ROOT_PASSWORD=$(openssl rand -hex 24)
ENCRYPTION_KEY=$EK
BASE_URL=http://localhost:3001
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
JWT_PRIVATE_KEY_PATH=/app/keys/private.pem
JWT_PUBLIC_KEY_PATH=/app/keys/public.pem
INVITE_CODE_REQUIRED=false
AUTO_VERIFY_EMAIL=true
RUST_LOG=nyxid=info,tower_http=info
EOF
ln -sf .env.dev .env.production

mkdir -p keys
openssl genrsa -out keys/private.pem 4096 2>/dev/null
openssl rsa -in keys/private.pem -pubout -out keys/public.pem 2>/dev/null

docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d

# Wait for health
n=0
until curl -sf http://localhost:3001/health >/dev/null 2>&1; do
  n=$((n+1))
  if [ "$n" -ge 45 ]; then echo "Timed out — check: docker compose logs backend"; break; fi
  sleep 2
done
echo "Save your encryption key (needed if you reset the database): $EK"
```

**Save `$EK` somewhere safe** (1Password, sealed note, anywhere not in this repo). If you nuke the Mongo volume, you need it to decrypt existing credentials. Without it, you re-register everything.

Verify:

```bash
curl -sf http://localhost:3001/health    # expect: 200
curl -I http://localhost:3000             # expect: 200
```

---

## Step 5 — Register your NyxID account and install the CLI

1. Open `http://localhost:3000` in a browser on the 4060 (or SSH-tunnel from the Mac: `ssh -L 3000:localhost:3000 -L 3001:localhost:3001 user@4060-ip`)
2. Click Register, use your real email, set a password
3. After login, navigate to **Settings** and create an API access token — save it

Install the CLI:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/ChronoAIProject/NyxID/main/skills/nyxid/tools/install.sh)"
source ~/.cargo/env
nyxid login --base-url http://localhost:3001
nyxid --version    # expect: a version string
```

---

## Step 6 — Register the mempalace shim as a NyxID service

This is the load-bearing step and the one we have NOT yet rehearsed on the Mac. Expect to iterate.

The intent: tell NyxID "there is an HTTP API at http://127.0.0.1:8765 that exposes these endpoints; expose them to MCP clients as tools called `mempalace_status` etc." NyxID's `nyxid service add` (or the dashboard) is where this happens.

Two possible flows (try in this order):

**Flow A — auto-import from OpenAPI:**

The host_server.py FastAPI app exposes `/openapi.json` automatically. If NyxID supports importing services from an OpenAPI URL, this is one command:

```bash
nyxid service add mempalace --openapi-url http://127.0.0.1:8765/openapi.json
nyxid service list
```

Expected: `mempalace` shows up with N endpoints (for v0.2 alpha, just 1 — `mempalace_status`).

**Flow B — manual endpoint registration (if Flow A is not supported):**

Use the dashboard at `http://localhost:3000` → AI Services → Add Service. Manually configure:
- Name: `mempalace`
- Base URL: `http://127.0.0.1:8765`
- Endpoint: `POST /v1/tools/mempalace_status`, MCP tool name `mempalace_status`, no params

Verify either way:

```bash
nyxid proxy request mempalace mempalace_status   # or whatever the actual subcommand turns out to be
```

You should get back the same JSON the curl in Step 2 returned, but now routed through NyxID. If you do — **the architecture works.**

**If Flow A fails:** check `docs/AI_AGENT_PLAYBOOK.md` and `docs/MCP_DELEGATION_FLOW.md` in the NyxID repo for the actual service registration shape. The README's `nyxid service add llm-openai` example is for an LLM provider, not a generic REST service — the syntax may differ.

---

## Step 7 — Get a remote MCP client to call it

The whole point: Claude Code on the Mac (NOT the 4060) should be able to use the mempalace tools as if they were local.

On the 4060, in the NyxID dashboard, go to **Settings > MCP** and copy the MCP config snippet for Claude Code. It will look something like:

```json
{
  "mcpServers": {
    "nyxid": {
      "url": "http://localhost:3001/api/v1/mcp",
      "headers": { "Authorization": "Bearer <delegation_token>" }
    }
  }
}
```

Two options for getting that snippet to the Mac:

**Option 1 — same LAN, no public domain:** SSH-tunnel the NyxID backend port from the Mac:

```bash
# on the Mac
ssh -L 3001:localhost:3001 user@4060-ip
```

Then use `http://localhost:3001/api/v1/mcp` in the Claude Code MCP config on the Mac. The Mac's traffic flows: Mac Claude Code → SSH tunnel → NyxID on 4060 → mempalace shim on 4060.

**Option 2 — proper public deployment:** put the NyxID backend behind Caddy/Nginx with TLS on a domain. Out of scope for this runbook — see `docs/DEPLOYMENT.md` in the NyxID repo. Do this only if you actually need internet-wide reach. For "Lexa's two machines" use case, Option 1 is enough.

Add the config to `~/.claude.json` (or `~/Library/Application Support/Claude/claude_code_config.json` — wherever Claude Code reads MCP servers from on the Mac), restart Claude Code, and in a new session ask the assistant to call `mempalace_status`. If a tool call shows up in the UI and returns palace data from the 4060, **you are done.**

---

## Success criteria checklist

Tick each as you verify:

- [ ] `curl http://127.0.0.1:8765/v1/tools/mempalace_status` on the 4060 returns valid JSON (Step 2)
- [ ] `systemctl --user status mempalace-sync-host` shows active running (Step 3)
- [ ] `curl http://localhost:3001/health` returns 200 (Step 4)
- [ ] You can log into the NyxID web console at `http://localhost:3000` (Step 5)
- [ ] `nyxid service list` includes `mempalace` (Step 6)
- [ ] A proxy call through NyxID returns palace data (Step 6)
- [ ] Mac Claude Code can call `mempalace_status` via the NyxID MCP config and get back data from the 4060 (Step 7)

When all seven are ticked, v0.2 alpha is real. Tag a release, write a blog post, ship it.

---

## Next steps after this runbook succeeds

1. **Backfill the other 18 tools.** Codex builds the full set of REST endpoints in `host_server.py` mirroring `mempalace/mcp_server.py`'s `TOOLS` dict. Each one is ~10 lines. Re-register the service so NyxID picks up the new OpenAPI surface.
2. **Per-agent isolation test.** Create two NyxID delegation tokens, give each to a different agent context, verify NyxID tags requests with distinct user IDs and that the shim sees the difference (we need to add a request log to the shim for this).
3. **Backups.** The palace at `$MEMPALACE_PALACE` is now a single point of failure. Set up either restic or borg to back up nightly to S3/B2.
4. **Telemetry.** Add a `/metrics` Prometheus endpoint to the shim so we can see request counts, latencies, and errors. Useful before any kind of public launch.

---

## Open questions to decide before running

These are not blockers but the runbook will be smoother if you have answers ready:

1. **4060 disk path for the palace.** Default in the runbook is `~/mempalace-data`. If you want a different mount point, change `MEMPALACE_PALACE` everywhere.
2. **NyxID accessibility.** SSH tunnel (Option 1, simple) or proper public domain (Option 2, complex)? Default to Option 1 unless you have a specific reason for Option 2.
3. **Account email.** You used `50111876+AlyciaBHZ@users.noreply.github.com` for git commits. For NyxID account registration, use your real email so password resets work. NyxID account ≠ git author.
4. **Existing palace data.** Are you starting the 4060 with a fresh empty palace, or do you want to seed it by rsync-ing your Mac's `~/.mempalace` first? If seeding: `rsync -avz ~/.mempalace/ user@4060-ip:~/mempalace-data/` from the Mac BEFORE Step 3.

---

## If you get stuck

- **Shim won't import mempalace on Linux:** likely a chromadb wheel issue with Python 3.13. Stick with 3.11 or 3.12.
- **NyxID Docker stack won't come up:** `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend` is the first place to look. Most failures are env var mismatches.
- **`nyxid service add` syntax doesn't match Flow A:** fall back to Flow B (dashboard manual), and open an issue in the NyxID repo asking for OpenAPI auto-import if it's not supported yet.
- **Mac Claude Code doesn't see the MCP server:** confirm the SSH tunnel is up (`curl http://localhost:3001/health` from the Mac should work), confirm the auth header is correct, restart Claude Code fully (not just a new conversation).

If something is broken in a way this runbook does not cover, ping the assistant with the error output and the step number. Don't bash on for an hour.
