#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from datetime import datetime

BLOCK_PATHS = ("/dev/block/by-name", "/dev/block/bootdevice/by-name")
DEFAULT_PARTITIONS = ("boot", "recovery", "system", "vendor")


def run(cmd, timeout=300):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", f"timeout after {timeout} seconds", 1


def adb_available():
    _, _, code = run(["adb", "version"], timeout=10)
    return code == 0


def list_connected_devices():
    out, _, code = run(["adb", "devices"], timeout=10)
    if code != 0:
        return []

    devices = []
    for line in out.splitlines():
        if not line or line.startswith("List of devices"):
            continue
        serial, _, state = line.partition("\t")
        if state == "device":
            devices.append(serial)
    return devices


def discover_partition_paths():
    partitions = {}
    for base_path in BLOCK_PATHS:
        out, err, code = run(["adb", "shell", "ls", base_path], timeout=30)
        if code != 0:
            continue
        if "No such file" in out or "Permission denied" in out or "No such file" in err or "Permission denied" in err:
            continue

        entries = []
        for line in out.replace("\r", "\n").splitlines():
            entries.extend(part for part in line.split() if part not in {".", ".."})

        if entries:
            for part in entries:
                partitions.setdefault(part, f"{base_path}/{part}")
            break

    return partitions


def create_dump_dir(base_output_dir=None):
    root = base_output_dir or os.getcwd()
    dump_dir = os.path.join(
        root,
        "h18_dump_" + datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{os.getpid()}",
    )
    os.makedirs(dump_dir, exist_ok=True)
    return dump_dir


def dump_partitions(requested_partitions, base_output_dir=None, log=print):
    available_partitions = discover_partition_paths()
    if not available_partitions:
        log("No readable partition directory found on the connected device.")
        return None, 0

    dump_dir = create_dump_dir(base_output_dir)
    log(f"Dumping to: {dump_dir}")

    success_count = 0
    for part in requested_partitions:
        source_path = available_partitions.get(part)
        if not source_path:
            log(f"  Skipping missing partition: {part}")
            continue

        destination = os.path.join(dump_dir, f"{part}.img")
        log(f"Pulling {part}.img from {source_path} ...")
        _, err, code = run(["adb", "pull", source_path, destination], timeout=300)
        if code != 0:
            log(f"  WARNING: failed to pull {part}.img — {err or 'unknown error'}")
            continue

        if not os.path.exists(destination) or os.path.getsize(destination) == 0:
            log(f"  WARNING: {part}.img was created but is empty")
            continue

        log(f"  {part}.img saved.")
        success_count += 1

    return dump_dir, success_count


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Dump firmware partitions from a connected ADB device.")
    parser.add_argument(
        "--partitions",
        default=",".join(DEFAULT_PARTITIONS),
        help="Comma-separated partition list",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where the timestamped dump folder will be created",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    print("=== Alltheway H18 / Binqi H18 Dump Tool ===")

    if not adb_available():
        print("adb not found!")
        return 1
    print("adb OK")

    devices = list_connected_devices()
    if not devices:
        print("\nNo device detected. Put radio in recovery mode first!")
        print("Try: Power off → hold Volume Down + Power")
        return 1

    print("Connected devices:")
    for serial in devices:
        print(f"  {serial}")

    requested_partitions = [part.strip() for part in args.partitions.split(",") if part.strip()]
    dump_dir, success_count = dump_partitions(requested_partitions, args.output_dir)
    if dump_dir is None:
        return 1

    print(f"\nDone! {success_count}/{len(requested_partitions)} partitions dumped.")
    print("If boot.img exists, we can root it with Magisk.")
    return 0 if success_count else 1


if __name__ == "__main__":
    sys.exit(main())
