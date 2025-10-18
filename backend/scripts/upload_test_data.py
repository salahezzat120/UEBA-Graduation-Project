#!/usr/bin/env python
import argparse
import os
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter, Retry

DEF_URL = "http://127.0.0.1:8000/api/v1/data/upload-logs"
DEF_FILE = Path("backend/data/large_sample_logs.csv")

def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def main():
    ap = argparse.ArgumentParser(description="Upload CSV logs to the UEBA backend.")
    ap.add_argument("--url", default=os.environ.get("UEBA_UPLOAD_URL", DEF_URL),
                    help=f"API endpoint (default: {DEF_URL})")
    ap.add_argument("--file", type=Path, default=Path(os.environ.get("UEBA_UPLOAD_FILE", str(DEF_FILE))),
                    help=f"CSV path (default: {DEF_FILE})")
    args = ap.parse_args()

    if not args.file.exists():
        raise SystemExit(f"CSV not found: {args.file}")

    size = args.file.stat().st_size
    print(f"Uploading {args.file} ({human(size)}) to {args.url}")
    start = time.time()

    # requests Session with retries
    sess = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=["POST"],
        raise_on_status=False,
    )
    sess.mount("http://", HTTPAdapter(max_retries=retries))
    sess.mount("https://", HTTPAdapter(max_retries=retries))

    with args.file.open("rb") as f:
        files = {"file": (args.file.name, f, "text/csv")}
        try:
            print("Uploading data... this may take a moment.")
            resp = sess.post(args.url, files=files, timeout=600)
        except requests.RequestException as e:
            raise SystemExit(f"Request failed: {e}")

    elapsed = time.time() - start
    if resp.ok:
        try:
            payload = resp.json()
        except ValueError:
            payload = resp.text
        print("Data uploaded successfully!")
        print("Response:", payload)
    else:
        print(f"Error uploading data: HTTP {resp.status_code}")
        print(resp.text[:1000])

    print(f"Upload took {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
