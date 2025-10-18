#!/usr/bin/env python
import csv
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path

DEF_NUM_RECORDS = 200_000
DEF_NUM_USERS = 1_000
DEF_OUTPUT = Path("backend/data/large_sample_logs.csv")

ACTIVITIES = ["login", "file_access", "database_access", "logout", "permission_change"]
LOCATIONS = ["Egypt", "USA", "Canada", "Germany", "Japan", "Australia"]
RESULTS = ["success", "failed"]

def main():
    ap = argparse.ArgumentParser(description="Generate synthetic UEBA CSV logs.")
    ap.add_argument("--num-records", type=int, default=DEF_NUM_RECORDS)
    ap.add_argument("--num-users", type=int, default=DEF_NUM_USERS)
    ap.add_argument("--output", type=Path, default=DEF_OUTPUT)
    ap.add_argument("--start-date", type=str, default="2025-01-01", help="YYYY-MM-DD")
    ap.add_argument("--days", type=int, default=30, help="spread range in days")
    args = ap.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    users = [f"user_{i}" for i in range(args.num_users)]
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")

    with args.output.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "timestamp", "activity_type", "source_ip", "location", "result"])

        for i in range(args.num_records):
            if i % 10_000 == 0:
                print(f"Generated {i} records...")

            username = random.choice(users)
            timestamp = start_date + timedelta(seconds=random.randint(0, args.days * 24 * 3600))
            ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

            writer.writerow([
                username,
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                random.choice(ACTIVITIES),
                ip,
                random.choice(LOCATIONS),
                random.choice(RESULTS),
            ])

    print(f"Successfully generated {args.num_records} records in {args.output}")

if __name__ == "__main__":
    main()
