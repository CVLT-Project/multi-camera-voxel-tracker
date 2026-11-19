#!/usr/bin/env bash
# Install/refresh the user-level systemd service on the Pi and make it start at boot.
# No root needed (a user unit + loginctl enable-linger for your own account).
#
# Turn it off again with:  ssh admin@pi3 'systemctl --user disable --now laser-node'
#
# The node asks for SCHED_FIFO on its ALSA thread by default (--rt 50) and widens the ring when the
# account is not allowed to, so nothing here has to know about realtime. To turn the attempt off:
#   systemctl --user edit laser-node     ->   ExecStart=  /home/david/laser_node/target/release/laser-node --no-rt
set -euo pipefail

PI=${PI:-admin@pi3}

ssh "$PI" bash -s <<'EOF'
set -euo pipefail
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/laser-node.service <<'UNIT'
[Unit]
Description=laser_node: galvo X/Y via ALSA (PCM5102A) + laser on GPIO 12 (TTL)
After=sound.target
# No start rate limit: at boot the ALSA card can appear a moment after this unit
# starts, and the right behaviour is to keep trying rather than stay failed.
StartLimitIntervalSec=0

[Service]
ExecStart=%h/laser_node/target/release/laser-node
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable laser-node
systemctl --user restart laser-node
sleep 2
systemctl --user --no-pager status laser-node
# Stay running after logout / without a login session.
loginctl enable-linger "$(id -un)" 2>/dev/null || echo "note: enable-linger needs root on this setup"
EOF

# The laser line is a digital output on GPIO 12: above 0 in a SET is on, 0 is off. GPIO 12 has to be a
# plain output for that - no dtoverlay=pwm* line for it in /boot/firmware/config.txt (see HOWTO.md), and
# `laser_node --gpio 12` is the default.
#
# What the node does with a laser edge by default (no ExecStart flags needed):
#   --laser-delay       not given, so the node holds every edge back by its own ring delay - 0.33 ms at
#                       384 kHz with the default 64 frame period and 2 period buffer - because that is how
#                       long the position in the same SET takes to reach the DAC.
# To pin the spacing to a measured number instead, or to switch the moment a SET arrives:
#
#   systemctl --user edit laser-node     ->
#     ExecStart=
#     ExecStart=/home/david/laser_node/target/release/laser-node --laser-delay 400
#     ExecStart=/home/david/laser_node/target/release/laser-node --laser-delay 0
#
# `laser-node --get-delay` (or ./scripts/deploy.sh delay) prints the spacing a running node is applying.
