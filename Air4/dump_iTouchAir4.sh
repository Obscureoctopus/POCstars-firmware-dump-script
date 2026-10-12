#!/usr/bin/env bash
## dump_iTouchAir4.sh — dump SPI NOR flash from an iTouch Air 4 smartwatch
## Requires: flashrom

set -euo pipefail

PREFIX="${1:-firmware}"
PROGRAMMER="${PROGRAMMER:-ch341a_spi}"
# Optional SPI speed constraint (e.g., "spispeed=2M" for CH341A or Raspberry Pi)
SPEED_PARAM="${SPEED_PARAM:-}" 

# Format programmer argument strings cleanly
PROG_ARGS="${PROGRAMMER}"
if [[ -n "${SPEED_PARAM}" ]]; then
    PROG_ARGS="${PROGRAMMER}:${SPEED_PARAM}"
fi

command -v flashrom >/dev/null || { echo "[-] flashrom not installed"; exit 1; }

echo "[*] Detecting flash chip..."
# We parse the output to help the user find candidate chips
flashrom -p "${PROG_ARGS}" 2>&1 | tee "${PREFIX}_detect.log" || true

echo ""
read -rp "[?] Enter exact chip name from options above (Leave blank for auto-detect): " CHIP
CHIP_ARG=()
[[ -n "${CHIP}" ]] && CHIP_ARG=( -c "${CHIP}" )

echo "[*] Reading flash (Pass 1) -> ${PREFIX}_1.bin"
flashrom -p "${PROG_ARGS}" "${CHIP_ARG[@]}" -r "${PREFIX}_1.bin"

echo "[*] Reading flash (Pass 2) -> ${PREFIX}_2.bin"
flashrom -p "${PROG_ARGS}" "${CHIP_ARG[@]}" -r "${PREFIX}_2.bin"

echo "[*] Comparing dumps to ensure absolute integrity..."
if cmp "${PREFIX}_1.bin" "${PREFIX}_2.bin"; then
    echo "[+] Success! Dumps match exactly."
    mv "${PREFIX}_1.bin" "${PREFIX}.bin"
    rm "${PREFIX}_2.bin"
    sha256sum "${PREFIX}.bin" | tee "${PREFIX}.sha256"
else
    echo "[!] ERROR: Dumps differ! Signals are unstable."
    echo "[!] Troubleshooting steps:"
    echo "    1. Shorten your jumper wires."
    echo "    2. Lower the SPI speed (e.g., export SPEED_PARAM=\"spispeed=1M\")."
    echo "    3. Clean the chip pins with isopropyl alcohol and re-seat the clip."
    exit 1
fi
