#!/usr/bin/env bash
# Sync the sources to the Pi, build there, optionally run.
#
#   ./scripts/deploy.sh                 sync + build
#   ./scripts/deploy.sh run             sync + build + run the server in this terminal (stops the service first)
#   ./scripts/deploy.sh stop            stop the autostarted service
#   ./scripts/deploy.sh start           start it again
#   ./scripts/deploy.sh send 0.5 -0.25 1
#   ./scripts/deploy.sh get
#   ./scripts/deploy.sh delay                 # how far the running server holds a laser edge back
#
set -euo pipefail

PI=${PI:-admin@pi3}
SRC=$(cd "$(dirname "$0")/.." && pwd)
CARGO='export PATH=$HOME/.cargo/bin:$PATH'

rsync -a --delete --exclude target --exclude .git --exclude '*.pdf' "$SRC/" "$PI:laser_node/"

MODE=${1:-build}
case "$MODE" in
  build)
    ssh "$PI" "cd laser_node && $CARGO && cargo build --release"
    ;;
  run)
    ssh "$PI" 'systemctl --user stop laser-node 2>/dev/null || true'
    ssh -t "$PI" "cd laser_node && $CARGO && cargo build --release && exec ./target/release/laser-node"
    ;;
  stop)
    ssh "$PI" 'systemctl --user stop laser-node && systemctl --user --no-pager status laser-node || true'
    ;;
  start)
    ssh "$PI" 'systemctl --user start laser-node && sleep 1 && systemctl --user --no-pager status laser-node'
    ;;
  send)
    shift
    ssh "$PI" "cd laser_node && ./target/release/laser-node --send $*"
    ;;
  get)
    ssh "$PI" "cd laser_node && ./target/release/laser-node --get"
    ;;
  delay)
    ssh "$PI" "cd laser_node && ./target/release/laser-node --get-delay"
    ;;
  *)
    echo "unknown mode: $MODE" >&2
    exit 2
    ;;
esac
