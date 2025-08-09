import os
import time
import sys
import requests


def main() -> int:
    port = os.environ.get("PORT", "8080")
    url = f"http://127.0.0.1:{port}/healthz"
    for _ in range(10):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return 0
        except Exception:
            pass
        time.sleep(0.5)
    return 1


if __name__ == "__main__":
    sys.exit(main())
