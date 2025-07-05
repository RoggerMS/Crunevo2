# Error Monitoring with Sentry

The application can send error reports to [Sentry](https://sentry.io/). To enable it, define the following environment variables:

```
SENTRY_DSN=<your-dsn>
SENTRY_ENVIRONMENT=production   # optional
SENTRY_TRACES_RATE=0.0          # optional performance sampling
```

When `SENTRY_DSN` is set, the Flask app initializes Sentry with logging integration so unhandled exceptions are reported automatically. Adjust `SENTRY_TRACES_RATE` to capture performance data if desired.
