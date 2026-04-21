# Monitoring and logs

The project has a basic production-ready observability setup:

- Every response includes `X-Request-ID`.
- Logs include `request_id` for correlation.
- Non-static requests are logged through the `core.requests` logger.
- Sensitive auth/security events are logged through `security.audit`.
- `/health/` checks database and cache availability.
- Sentry can be enabled without code changes.

## Health check

Use this endpoint in uptime checks or platform health probes:

```text
GET /health/
```

Healthy response:

```json
{
  "status": "ok",
  "checks": {
    "database": true,
    "cache": true
  }
}
```

## Sentry

Create a Django project in Sentry, copy the DSN and configure production:

```env
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.05
SENTRY_SEND_DEFAULT_PII=false
RELEASE_VERSION=2026.04.21-1
```

Notes:

- Keep `SENTRY_SEND_DEFAULT_PII=false` unless there is a clear reason to send user-identifying data.
- Start with a low traces sample rate, for example `0.01` to `0.05`.
- Set `RELEASE_VERSION` during deploy so errors can be tied to a release.

## Log levels

```env
LOG_LEVEL=INFO
REQUEST_LOG_LEVEL=INFO
SECURITY_AUDIT_LOG_LEVEL=INFO
```

For noisy environments, set:

```env
REQUEST_LOG_LEVEL=WARNING
```
