#!/usr/bin/env bash
# How often does the ALSA thread actually fall behind, per ring/block configuration?
#
#   PI=david@rp4 ./scripts/bench-underrun.sh 192000:128:4:1 192000:64:4:1:50
#
# A configuration is rate:period:periods:block[:rt-prio]. They are joined with commas before they
# cross the ssh boundary, because a value containing spaces does not survive the second shell
# intact. 64 is the shortest period this driver allows, so that is the floor to bench against. An
# rt-prio of 0 means --no-rt, which is how the no-realtime fallback path gets measured at all - the
# node asks for realtime on its own these days.
#
# No client traffic at all: an underrun here is the machine missing the write deadline, not a
# control program misbehaving. One period of slack is what the writer has to be served; at
# 192 kHz a period is 0.33 ms, at 48 kHz 1.33 ms.
#
# RUN_SECONDS=120 per configuration. The node runs standalone; the autostart service is restored
# at the end. LOAD=1 drives it with scripts/demo.py (--endless --pattern lines, ~500 points/s)
# instead of leaving it idle, which is the case where a tight ring actually shows its price.
set -euo pipefail

PI=${PI:-admin@pi3}
RUN_SECONDS=${RUN_SECONDS:-120}
LOAD=${LOAD:-0}
CONFIGS=${*:-192000:128:4:1}
CONFIGS=$(echo $CONFIGS | tr ' ' ',')   # no spaces anywhere on the ssh command line

ssh "$PI" RUN_SECONDS="$RUN_SECONDS" LOAD="$LOAD" CONFIGS="$CONFIGS" 'bash -s' <<'EOF'
set -euo pipefail
LOAD=${LOAD:-0}
cd laser_node
BIN=./target/release/laser-node

systemctl --user stop laser-node 2>/dev/null || true
# Do not leave a node holding the ALSA card, or the autostart service loops on "Device or resource busy".
trap 'pkill -x laser-node 2>/dev/null || true; sleep 1; systemctl --user start laser-node 2>/dev/null || true' EXIT

for cfg in ${CONFIGS//,/ }; do
  IFS=: read -r rate period ring block prio <<< "$cfg"
  extra=""
  if [ -n "${prio:-}" ]; then
    if [ "$prio" = 0 ]; then extra="--no-rt"; else extra="--rt $prio"; fi
  fi
  log=/tmp/underrun.log
  : > "$log"
  pkill -x laser-node 2>/dev/null || true
  sleep 1
  $BIN --rate "$rate" --period "$period" --periods "$ring" --block "$block" $extra >"$log" 2>&1 &
  pid=$!
  sleep 3
  frames=$(grep -oE 'buffer = [0-9]+ frames' "$log" | grep -oE '[0-9]+' || true)
  period=$(grep -oE 'period = [0-9]+ frames' "$log" | grep -oE '[0-9]+' || true)
  if [ -z "$frames" ]; then echo "rate=$rate period=$period: the node did not start, see $log"; cat "$log"; continue; fi
  period_ms=$(awk -v p="$period" -v r="$rate" 'BEGIN { printf "%.2f", p * 1000 / r }')
  deadline_ms=$(awk -v b="$block" -v p="$period" -v r="$rate" 'BEGIN { printf "%.2f", b * p * 1000 / r }')
  lat_ms=$(awk -v f="$frames" -v r="$rate" 'BEGIN { printf "%.2f", f * 1000 / r }')
  if [ "$LOAD" = 1 ]; then
    timeout "$RUN_SECONDS" python3 scripts/demo.py --endless --pattern lines >/dev/null 2>&1 || true
  else
    sleep "$RUN_SECONDS"
  fi
  xruns=$(grep -c 'Broken pipe' "$log" || true)
  short=$(grep -c 'short write' "$log" || true)
  cpu=$(ps -o pcpu= -p "$pid" 2>/dev/null | tr -d ' ')
  rt=$(grep -oE 'SCHED_FIFO priority [0-9]+|SCHED_FIFO [0-9]+: [A-Za-z ]+|no realtime priority' "$log" | head -1 || true)
  kill "$pid" 2>/dev/null
  echo "rate=$rate ring=${frames}f/${lat_ms}ms block=${block}p (${deadline_ms} ms deadline, load=${LOAD}): underruns=$xruns shortwrites=$short cpu=${cpu}% scheduling=${rt:-not requested}"
  grep -E 'Broken pipe|short write' "$log" | head -2 | sed 's/^/    /' || true
done
EOF
