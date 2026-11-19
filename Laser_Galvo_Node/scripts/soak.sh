#!/usr/bin/env bash
# Soak test on the Pi: send random setpoints, then report ALSA errors, CPU/RSS and the laser pin.
#
#   ./scripts/soak.sh                                   (RUN_SECONDS=60 PI=admin@pi3)
#   PI=david@rp4 ./scripts/soak.sh --periods 4 --block 1   # extra flags go straight to the node
#   PI=david@rp4 ./scripts/soak.sh --rate 384000
#   PI=david@rp4 HARSH=1 ./scripts/soak.sh                 # a client process per setpoint
#
# Default load is one open connection with one line per setpoint - that is what a control program
# does. HARSH=1 is the pathological version: a new client process per setpoint, which makes the
# node create a thread per connection and is the only configuration where the ALSA thread was ever
# seen to fall behind.
set -euo pipefail

PI=${PI:-admin@pi3}
RUN_SECONDS=${RUN_SECONDS:-60}
CMDS=$((RUN_SECONDS * 50))
HARSH=${HARSH:-0}

# Whatever is left on the command line is handed to the node on the Pi, as separate words after
# "bash -s --": a single value containing spaces does not survive the second shell intact.
ssh "$PI" RUN_SECONDS="$RUN_SECONDS" CMDS="$CMDS" HARSH="$HARSH" 'bash -s --' "$@" <<'EOF'
set -euo pipefail
cd laser_node
BIN=./target/release/laser-node
SOCK=/tmp/laser.sock

# This test runs its own node, so the autostarted one has to get out of the way: the ALSA
# device is exclusive and two instances just fight over it.
systemctl --user stop laser-node 2>/dev/null || true
# Whatever happens, do not leave our node holding the ALSA card: the autostart service would sit in
# an auto-restart loop against it.
restart_service() {
  if [ -n "${NODE:-}" ]; then kill "$NODE" 2>/dev/null || true; fi
  pkill -x laser-node 2>/dev/null || true
  sleep 1
  systemctl --user start laser-node 2>/dev/null || true
}
trap restart_service EXIT

# The PCM5102A card exposes no xruns_ counter in /proc on this kernel, so the evidence for an
# underrun is the node's own log ("Broken pipe", "short write") plus the delay the kernel keeps
# for the live stream: how far behind the DAC the writer currently is, in frames.
# The analog DAC is not necessarily card 0: a loopback module loaded at boot takes index 0 and
# pushes the HiFiBerry to 1, so pick the card that is neither loopback nor HDMI.
DAC=$(grep -E '^ *[0-9]+ \[' /proc/asound/cards | grep -ivE 'loopback|hdmi' | head -1 | sed 's/^ *//; s/ .*//')
DAC=${DAC:-0}
sub0() {
  f=/proc/asound/card$DAC/pcm0p/sub0/status
  if [ -r "$f" ] && [ "$(cat "$f")" != "closed" ]; then
    grep -E 'state|delay|avail' "$f" | sed 's/^/  /'
  else
    echo "  (no live substream)"
  fi
}

pkill -x laser-node 2>/dev/null || true
sleep 0.5
./target/release/laser-node "$@" > /tmp/laser.log 2>&1 &
NODE=$!
sleep 2
if ! kill -0 "$NODE" 2>/dev/null; then
  echo "the node died at startup, log follows:" >&2
  cat /tmp/laser.log >&2
  exit 1
fi

echo "--- hw_params in the kernel:"
grep -E 'format|rate|period_size|buffer_size' /proc/asound/card$DAC/pcm0p/sub0/hw_params | sed 's/^/  /'
echo "--- stream at start:"
sub0

if [ "$HARSH" = "1" ]; then
  echo "--- load: $CMDS setpoints, one client process each"
  awk -v n="$CMDS" 'BEGIN { srand(7); for (i = 0; i < n; i++) printf "%.3f %.3f %d\n", rand()*2-1, rand()*2-1, (rand() > 0.5) }' \
    | while read x y p; do $BIN --send "$x" "$y" "$p" > /dev/null; sleep 0.02; done
else
  echo "--- load: $CMDS setpoints on one open connection"
  python3 - "$SOCK" "$CMDS" <<'PY'
import random, socket, sys, time
sock_path, n = sys.argv[1], int(sys.argv[2])
random.seed(7)
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(sock_path)
for i in range(n):
    s.sendall(f"SET {random.uniform(-1,1):.3f} {random.uniform(-1,1):.3f} {1 if random.random() > 0.5 else 0}\n".encode())
    time.sleep(0.02)
PY
fi

$BIN --socket "$SOCK" --send 1 1 1
sleep 1
echo "--- stream after $RUN_SECONDS s of random setpoints:"
sub0
echo "--- laser pin while power = 1 (expect 'hi' on an output):"
pinctrl get 12 2>&1 | head -2 || true
echo "--- the node's laser edge spacing:"
$BIN --socket "$SOCK" --get-delay
echo "--- resources:"
ps -o pcpu,rss,etime,comm -C laser-node
echo "--- log lines mentioning ALSA: $(grep -c ALSA /tmp/laser.log || true)"
echo "--- underrun evidence (Broken pipe / short write): $(grep -cE 'Broken pipe|short write' /tmp/laser.log || true)"
grep -E 'Broken pipe|short write' /tmp/laser.log | head -3 | sed 's/^/  /'
$BIN --socket "$SOCK" --send 0 0 0
sleep 1
echo "--- laser pin while power = 0 (expect 'lo'):"
pinctrl get 12 2>&1 | head -2 || true
pkill -x laser-node
echo "--- stopped, autostart service re-enabled"
EOF
