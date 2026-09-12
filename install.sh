#!/usr/bin/env bash
# sup-agent — bir buyruqli o'rnatuvchi (Linux systemd / macOS launchd).
#
# Reponi klonlagach, SHU papkadan:
#   export SUP_FLEET_KEY='<markazda: agent hub key>'
#   export SUP_NODE_NAME='face'          # ixtiyoriy
#   bash install.sh
#
# Hammasini o'zi qiladi: config (kalit MUHITDAN, chmod 600), ulanish sinovi,
# autostart (Restart=always + boot), majburiy kill-sinovi (REBOOT EMAS),
# sir-himoya tekshiruvi va hisobot. Idempotent: qayta ishga tushirsa xavfsiz.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

log() { printf '\n[install] %s\n' "$*"; }
die() { printf '\n[install] XATO: %s\n' "$*" >&2; exit 1; }

# 0) Fleet kaliti: MUHITDAN yoki KALIT FAYLIDAN (~/.sup_key yoki ./.sup_key).
#    Fayl — markazdan `scp .fleet-key user@host:~/.sup_key` bilan tashilgan sir.
#    Shunday qilingani uchun agentning "yangi shell" muhiti muhim emas: skript
#    kalitni fayldan o'qiydi va config yozilgach faylni O'CHIRADI.
KEYFILE=""
if [ -z "${SUP_FLEET_KEY:-}" ]; then
  for f in "$HOME/.sup_key" "$HERE/.sup_key"; do
    if [ -f "$f" ]; then
      SUP_FLEET_KEY="$(tr -d '\r\n' < "$f")"
      export SUP_FLEET_KEY
      KEYFILE="$f"
      break
    fi
  done
fi
[ -n "${SUP_FLEET_KEY:-}" ] || die "fleet kaliti yo'q (muhitda ham, ~/.sup_key da ham).
  Markazdan:  scp .fleet-key <user>@<host>:~/.sup_key
  yoki:       export SUP_FLEET_KEY='...'   (kalitni chatga yozmang)"

# 1) Talablar
command -v python3 >/dev/null || die "python3 yo'q (apt install -y python3)"
command -v git >/dev/null || die "git yo'q (apt install -y git)"
PY="$(command -v python3)"

SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
NODE_USER="${SUDO_USER:-$(id -un)}"     # servis shu foydalanuvchi ostida ishlaydi
OS="$(uname -s)"

# 2) config.json (kalit muhitdan; qiymati hech qayerda ko'rsatilmaydi)
#    Nom berilmasa - hostname (masalan "face").
export SUP_NODE_NAME="${SUP_NODE_NAME:-$(hostname -s 2>/dev/null || hostname)}"
[ -f config.json ] || cp config.example.json config.json
"$PY" setup_config.py || die "config yozilmadi"
chmod 600 config.json
# Kalit endi config.json da (600) — vaqtincha kalit faylini o'chiramiz.
if [ -n "$KEYFILE" ]; then rm -f "$KEYFILE" && log "kalit fayli o'chirildi: $KEYFILE"; fi

# 3) Ulanish sinovi
log "ulanish sinovi: node.py --once"
"$PY" node.py --once || die "markazga ulanmadi - kalit yoki tarmoqni tekshiring"

# 4) Autostart
if [ "$OS" = "Linux" ]; then
  command -v systemctl >/dev/null || die "systemd yo'q - docs/O'RNATISH.md §5 qo'lda"
  UNIT=/etc/systemd/system/sup-agent.service
  log "systemd birligi: $UNIT (User=$NODE_USER)"
  $SUDO tee "$UNIT" >/dev/null <<EOF
[Unit]
Description=sup-agent (markaziy agent node)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$NODE_USER
WorkingDirectory=$HERE
ExecStart=$PY $HERE/node.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  $SUDO systemctl daemon-reload
  $SUDO systemctl enable --now sup-agent
  AUTOSTART="systemd"
elif [ "$OS" = "Darwin" ]; then
  PLIST="$HOME/Library/LaunchAgents/uz.1pro.supagent.plist"
  mkdir -p "$HOME/Library/LaunchAgents"
  log "launchd: $PLIST"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>uz.1pro.supagent</string>
  <key>ProgramArguments</key><array>
    <string>$PY</string><string>$HERE/node.py</string>
  </array>
  <key>WorkingDirectory</key><string>$HERE</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>/tmp/supagent.err</string>
  <key>StandardOutPath</key><string>/tmp/supagent.out</string>
</dict></plist>
EOF
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load -w "$PLIST"
  AUTOSTART="launchd"
else
  die "bu skript Linux/macOS uchun. Windows: docs/O'RNATISH.md §5 (Task Scheduler)"
fi

# 5) MAJBURIY TEKSHIRUV — yoqilgan + o'zini-ko'tarish (REBOOT EMAS)
log "tekshiruv: yoqilganmi va o'ldirilsa o'zi ko'tariladimi"
if [ "$OS" = "Linux" ]; then
  systemctl is-enabled sup-agent | grep -q enabled || die "is-enabled != enabled"
  systemctl is-active  sup-agent | grep -q active  || die "is-active != active"
  OLDPID="$($SUDO systemctl show -p MainPID --value sup-agent)"
  $SUDO systemctl kill -s KILL sup-agent || true
  sleep 8
  systemctl is-active sup-agent | grep -q active || die "o'ldirilgach ko'tarilmadi"
  NEWPID="$($SUDO systemctl show -p MainPID --value sup-agent)"
  log "o'zini-ko'tardi (PID $OLDPID -> $NEWPID)"
else
  launchctl list | grep -q uz.1pro.supagent || die "launchd ro'yxatda yo'q"
  PID="$(launchctl list | awk '/uz.1pro.supagent/{print $1}')"
  [ "${PID:-}" != "-" ] && [ -n "${PID:-}" ] && kill -9 "$PID" 2>/dev/null || true
  sleep 8
  launchctl list | grep -q uz.1pro.supagent || die "o'ldirilgach ko'tarilmadi"
  log "o'zini-ko'tardi"
fi

# 6) Sir himoyasi
PERM="$(stat -c '%a' config.json 2>/dev/null || stat -f '%Lp' config.json)"
[ "$PERM" = "600" ] || die "config.json ruxsati $PERM (600 kerak)"
git check-ignore config.json >/dev/null || die "config.json git da ko'rinyapti (.gitignore buzuq)"

# 7) Hisobot
NAME="$("$PY" -c 'import json;print(json.load(open("config.json")).get("name",""))')"
NID="$("$PY" -c 'import json;print(json.load(open("config.json")).get("node_id",""))')"
log "TUGADI"
printf "node: %s (%s) · %s · autostart: %s · tekshiruv: yoqilgan=ha, o'zini-ko'tardi=ha, sir-himoya=ha (config.json 600, git da yo'q)\n" \
  "$NAME" "$NID" "$OS" "$AUTOSTART"
