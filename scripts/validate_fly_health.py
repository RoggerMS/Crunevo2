import sys
from pathlib import Path

try:
    import tomllib as tomli  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli

sys.path.append(str(Path(__file__).resolve().parents[1]))
from crunevo.config import Config


def main() -> int:
    data = tomli.loads(Path("fly.toml").read_text("utf-8"))
    checks = data.get("http_service", {}).get("checks", [])
    path = checks[0]["path"] if checks else None
    if path != Config.HEALTH_PATH:
        print(f"fly.toml health check path {path!r} != {Config.HEALTH_PATH!r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
