# Redis Rules

## Redis Usage

Redis Cluster is used for cache and session support. Local nodes run on ports `7001` through `7006`.

Typical backend uses:
- Spring Session storage after login.
- Cache for frequently read data.
- Distributed state where already designed.

## Configuration

- Keep Redis nodes configurable through properties or environment variables.
- Use serializers intentionally. Prefer string keys and JSON-compatible values for cache entries unless existing code uses another format.
- Set TTLs for caches. Avoid permanent cache entries for mutable business data.
- Keep cache names specific, such as trips, routes, revenue summaries, or user sessions.

## Correctness

- Do not cache security-sensitive secrets.
- Do not cache stale authorization decisions unless the invalidation strategy is explicit.
- Invalidate or update cache entries after writes that change cached data.
- Session timeout must be consistent with authentication behavior.

## Troubleshooting

- Confirm all six Redis nodes are running.
- Confirm the app is using cluster configuration, not a single-node connection, when cluster mode is expected.
- For serialization errors, inspect key/value serializer configuration before changing domain objects.
- Do not edit Redis runtime data files manually.

