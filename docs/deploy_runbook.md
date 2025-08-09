# Deploy Runbook

## Deploying
1. Run `scripts/pre_deploy_check.sh` to verify health and HTTPS.
2. Deploy with `fly deploy`.

## Restarting Machines
```
fly scale count 1
```
Adjust the count as needed.

## Testing Health Endpoint via SSH
```
fly ssh console -C "curl -i $HEALTH_PATH"
```

## Recovering from Failed Health Checks
1. Check logs: `fly logs`.
2. Verify secrets and config.
3. Ensure `/healthz` returns `{\"status\":\"ok\"}`.
4. Redeploy or restart after fixing issues.
