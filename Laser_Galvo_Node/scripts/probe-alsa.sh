#!/usr/bin/env bash
# What does the DAC card actually accept, and what is the running node using?
# Run this before believing any latency number, and after every rate/period change.
#
#   PI=david@rp4 ./scripts/probe-alsa.sh
#
# The card is exclusive, so the node is stopped for the probe and started again at the end.
# Nothing is written to the outputs: --dump-hw-params asks for ranges and aborts.
set -euo pipefail

PI=${PI:-admin@pi3}

ssh "$PI" 'bash -s' <<'EOF'
set -euo pipefail
systemctl --user stop laser-node 2>/dev/null || true
sleep 0.5

echo "=== cards ==="
cat /proc/asound/cards

for idx in $(awk '/^ *[0-9]+ /{print $1}' /proc/asound/cards); do
  echo "=== hw:$idx accepted ranges (playback) ==="
  # aplay, not arecord: a DAC-only card has no capture substream at all (/dev/snd has no
  # pcmC0D0c), which shows up as the confusing "audio open error: No such file or directory".
  # --dump-hw-params asks for the ranges and aborts before any sample is transferred, and stdin
  # is empty on top of that.
  aplay -q -D "hw:$idx" --dump-hw-params </dev/null 2>&1 \
    | grep -E 'ACCESS|FORMAT|CHANNELS|RATE|BUFFER|PERIOD' || echo "  (card $idx did not open)"
done

echo "=== starting the node with its defaults ==="
systemctl --user start laser-node
sleep 2
journalctl --user -u laser-node -n 12 --no-pager 2>/dev/null | grep -i alsa || true

echo "=== live hw_params and underrun counters ==="
for f in /proc/asound/card*/pcm*p/sub0/hw_params /proc/asound/card*/pcm*p/sub0/status; do
  [ -r "$f" ] || continue
  echo "-- $f"
  cat "$f" | grep -E 'access|format|channels|rate|period_size|buffer_size|xruns|overrun|underrun|state' || true
done
EOF
