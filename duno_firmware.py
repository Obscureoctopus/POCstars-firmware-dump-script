import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--partitions", default="boot,recovery,system,vendor", help="Comma-separated list")
args = parser.parse_args()
partitions = [p.strip() for p in args.partitions.split(",") if p.strip() in ALLOWED_PARTITIONS]
