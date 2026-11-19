#!/usr/bin/env bash
# Everything that can be checked without a Pi: the Rust unit tests and the three Python ones.
#
#   ./scripts/tests/run.sh
#
# What needs the hardware is in scripts/soak.sh, scripts/test-loopback.sh and scripts/bench-underrun.sh.
set -euo pipefail
cd "$(dirname "$0")/../.."

export PATH="$HOME/.cargo/bin:$PATH"
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test

for t in test-svg test-orient test-mouse; do
  echo "--- scripts/tests/$t.py"
  python3 "scripts/tests/$t.py" > /tmp/$t.log
  tail -1 /tmp/$t.log
done
echo "all green"
