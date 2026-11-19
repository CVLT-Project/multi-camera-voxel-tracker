#!/usr/bin/env bash
# Bench test of the ALSA path without a DAC on the pins.
# The loopback driver echoes what we write, so the i16 samples that would go to the
# PCM5102A can be read back exactly - including the ramp between two setpoints.
#
# Needs once as root: sudo modprobe snd-aloop
#
# Expected: a held setpoint comes out as a flat line, and a step command comes out as a monotone
# ramp that lands exactly on the target - no overshoot, no ringing, no drift.
#
# Measured on rp4 (2026-11-16), so do not read this rig as a health test of the node: with the
# loopback card the node either sat in continuous "Broken pipe" (192 kHz, period 128/64, ring 4-16,
# hw:3 and plughw:3, arecord before or after the node) or the capture side reported pure silence.
# The loopback pair only mirrors data when both sides reach RUNNING together, which this SoC driver
# pairing does not manage; the real DAC card (hw:0) runs the same code cleanly. Sample-level proof
# of the ramp therefore comes from the unit tests in src/main.rs, and the analog proof from the
# multimeter. Keep this script for a card that does behave, and check /proc/asound/cards for the
# loopback index first.
#
# This is only for debugging without hardware. With the breakout wired up, measure the
# DAC outputs with a multimeter instead (see README.md).
set -euo pipefail

PI=${PI:-admin@pi3}
CARD=${CARD:-2}   # loopback card index, check with: ssh admin@pi3 cat /proc/asound/cards
NODE_RATE=${NODE_RATE:-}   # e.g. NODE_RATE=48000 if the loopback card dislikes 192 kHz

ssh "$PI" CARD="$CARD" NODE_RATE="$NODE_RATE" 'bash -s' <<'EOF'
set -euo pipefail
cd laser_node
BIN=./target/release/laser-node
SOCK=/tmp/laser-test.sock

if ! grep -qi loopback /proc/asound/cards; then
  echo "no loopback card on the Pi - run 'sudo modprobe snd-aloop' first" >&2
  exit 1
fi

pkill -x laser-node 2>/dev/null || true
sleep 0.5
EXTRA=""
if [ -n "$NODE_RATE" ]; then EXTRA="--rate $NODE_RATE"; fi
$BIN --device "hw:$CARD" --socket "$SOCK" $EXTRA > /tmp/laser-test.log 2>&1 &
sleep 1
RATE=$(grep -oE 'ALSA: [0-9]+ Hz' /tmp/laser-test.log | grep -oE '[0-9]+')
PERIOD=$(grep -oE 'period = [0-9]+ frames' /tmp/laser-test.log | grep -oE '[0-9]+')
echo "node reports: ${RATE} Hz, period ${PERIOD} frames"

$BIN --socket "$SOCK" --send 0 0 0 > /dev/null
sleep 0.2
# Record first, then change the setpoint: the ramp is 1-2 periods long, so it would be
# over before arecord gets going the other way round.
arecord -q -D "hw:$CARD" -f S16_LE -c 2 -r "$RATE" -d 1 /tmp/setpoint.raw &
REC=$!
sleep 0.15
$BIN --socket "$SOCK" --send 0.5 -0.25 0 > /dev/null   # 16384 / -8192
wait "$REC"

python3 - "$RATE" "$PERIOD" <<'PY'
import array, sys
rate, period = int(sys.argv[1]), int(sys.argv[2])
a = array.array('h'); a.frombytes(open('/tmp/setpoint.raw', 'rb').read())
x, y = list(a[0::2]), list(a[1::2])
# The loopback hands back whatever was left in the ring before the writer got going, so the
# first moments are not ours to judge. Skip 50 ms of it.
skip = rate // 20
x, y = x[skip:], y[skip:]
print(f"{len(x)} frames recorded at {rate} Hz")

def check(name, samples, target):
    start = samples[0]
    assert start != target, f"{name}: the ramp was over before recording started"
    assert samples[:period] == [start] * period, f"{name}: no flat start at {start}"
    bad = [s for s in samples if not min(start, target) <= s <= max(start, target)]
    assert not bad, f"{name}: samples outside {start}..{target}: {bad[:5]}"
    # one transition: never changes direction
    diffs = [b - s for s, b in zip(samples, samples[1:]) if b != s]
    assert all(d > 0 for d in diffs) or all(d < 0 for d in diffs), f"{name}: not monotone"
    moving = [i for i, s in enumerate(samples) if start < s < target] if start < target \
             else [i for i, s in enumerate(samples) if target < s < start]
    span = (moving[-1] - moving[0] + 2) if moving else 1
    tail = samples[-period:]
    assert tail == [target] * period, f"{name}: tail is not flat at {target}: {tail[:8]}"
    slope = -(-abs(target - start) // period)  # ceil, i.e. the ramp's steepest legal step
    worst = max((abs(b - s) for s, b in zip(samples, samples[1:])), default=0)
    assert worst <= slope, f"{name}: a frame moved {worst}, the ramp allows {slope}"
    print(f"{name}: {start} -> {target}, ramp spans {span} frames (period {period}), "
          f"flat tail ok, steepest frame step {worst}")

check("X", x, 16384)   # round(0.5  * 32767)
check("Y", y, -8192)   # round(-0.25 * 32767)
print("ramp ok")
PY

pkill -x laser-node
EOF
