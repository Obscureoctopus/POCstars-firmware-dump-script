#!/usr/bin/env python3
import subprocess
import os
import sys
from datetime import datetime

print("=== Alltheway H18 / Binqi H18 Dump Tool ===")

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

# Check adb
out, err, code = run("adb version")
if code != 0:
    print("adb not found!")
    sys.exit(1)
print("adb OK")

# Check device
out, err, code = run("adb devices")
print(out)

if "device" not in out:
    print("\nNo device detected. Put radio in recovery mode first!")
    print("Try: Power off → hold Volume Down + Power")
    sys.exit(1)

# Dump folder
dump_dir = "h18_dump_" + datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(dump_dir, exist_ok=True)
print(f"\nDumping to: {dump_dir}")

# Pull the important files
for part in ["boot", "recovery", "system"]:
    print(f"Pulling {part}.img ...")
    run(f"adb pull /dev/block/by-name/{part} {dump_dir}/{part}.img")

print("\nDone! Check the folder for the .img files.")
print("If boot.img exists, we can root it with Magisk.")
