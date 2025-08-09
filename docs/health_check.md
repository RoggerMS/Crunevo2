# Health Check Configuration

Fly.io monitors the app using `/healthz`.

## Default Check

```
[[http_service.checks]]
  method = "GET"
  path = "/healthz"
  interval = "10s"
  timeout = "5s"
  grace_period = "90s"
```

## Modifying the Path

1. Update `HEALTH_PATH` in `crunevo/config.py` or via env.
2. Update `fly.toml` `[[http_service.checks]]` path to match.
3. Run `python scripts/validate_fly_health.py` to confirm configuration.
4. Commit both changes together to avoid broken deploys.

Always ensure `/healthz` responds with JSON `{ "status": "ok" }` and HTTP 200.
