#!/usr/bin/env python3
import subprocess
import os
import sys
from datetime import datetime

print("=== Alltheway H18 / Binqi H18 Dump Tool ===")

def run(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        print(f"  ERROR: command timed out after 300 seconds: {' '.join(cmd)}")
        return "", "timeout", 1

# Check adb
out, err, code = run(["adb", "version"])
if code != 0:
    print("adb not found!")
    sys.exit(1)
print("adb OK")

# Check device
out, err, code = run(["adb", "devices"])
print(out)

# A connected device shows a line like "<serial>\tdevice" after the header.
# Simply checking for "device" in the full output would match the header
# "List of devices attached", so we inspect each non-header line instead.
device_connected = any(
    "\tdevice" in line
    for line in out.splitlines()
    if not line.startswith("List of devices")
)
if not device_connected:
    print("\nNo device detected. Put radio in recovery mode first!")
    print("Try: Power off → hold Volume Down + Power")
    sys.exit(1)

# Dump folder — include PID to avoid collisions when multiple instances run
dump_dir = "h18_dump_" + datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{os.getpid()}"
os.makedirs(dump_dir, exist_ok=True)
print(f"\nDumping to: {dump_dir}")

# Pull the important files
ALLOWED_PARTITIONS = {"boot", "recovery", "system"}
for part in ["boot", "recovery", "system"]:
    if part not in ALLOWED_PARTITIONS:
        print(f"  Skipping unknown partition: {part}")
        continue
    print(f"Pulling {part}.img ...")
    out, err, code = run(["adb", "pull", f"/dev/block/by-name/{part}", f"{dump_dir}/{part}.img"])
    if code != 0:
        print(f"  WARNING: failed to pull {part}.img — {err or 'unknown error'}")
    else:
        print(f"  {part}.img saved.")

print("\nDone! Check the folder for the .img files.")
print("If boot.img exists, we can root it with Magisk.")
