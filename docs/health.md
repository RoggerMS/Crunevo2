# Health Endpoints Runbook

## Endpoints
- `/healthz`: basic liveness check, returns `ok` and header `X-App-Revision` from `GIT_SHA`.
- `/live`: returns JSON `{"status": "live"}`.
- `/ready`: returns JSON `{"status": "ready"}`.

## Security Exemptions
- CSRF protection is disabled for the health blueprint.
- When Talisman is enabled, these routes are explicitly exempt from HTTPS enforcement.

## Fly.io Alignment
- The health check path is defined in `crunevo.config.Config.HEALTH_PATH`.
- `scripts/validate_fly_health.py` ensures `fly.toml` checks use the same path.

## Operations
- Scale app to zero and back to force a clean start when troubleshooting.
- Use `python scripts/smoke_check.py` or `make smoke` to verify a local deployment.

## Diagnostics
- `curl -i https://<app>/healthz`
- `fly checks list -a <APP>`
- `fly logs -a <APP>`
