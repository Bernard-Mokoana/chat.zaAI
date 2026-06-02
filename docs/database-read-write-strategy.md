# Database Read/Write Strategy

## Runtime Routing

The application uses two SQLAlchemy session factories:

- `SessionPrimary`: bound to `DATABASE_PRIMARY_URL`; use for all writes and for reads that must see a just-committed write.
- `SessionReplica`: bound to `DATABASE_REPLICA_URL` when replica reads are enabled; use for read-only routes that can tolerate normal replication lag.

FastAPI dependencies:

- `get_write_db()`: primary database session.
- `get_read_db()`: replica-safe read session. In local development it can fall back to primary.

Current routing:

- Auth register/login/refresh/logout: primary, because these flows write users or refresh-token audit rows.
- JWT user validation: primary for now, because protected session creation immediately after registration should not fail due to replica lag.
- Chat history retrieval: read session, because it is a read-only lookup by conversation id and authenticated owner.
- Worker message persistence and usage logging: primary, because workers write conversation, message, and usage rows.

## Environment Variables

```env
DATABASE_PRIMARY_URL=postgresql+psycopg://postgres:password@primary-host:5432/chatbot
DATABASE_REPLICA_URL=postgresql+psycopg://postgres:password@replica-host:5432/chatbot
DATABASE_READ_FROM_REPLICA=true
DATABASE_ALLOW_REPLICA_FALLBACK=true
```

`DATABASE_READ_FROM_REPLICA=false` forces all read sessions to primary. This is useful during maintenance, replica lag incidents, and local development.

`DATABASE_ALLOW_REPLICA_FALLBACK=true` allows `get_read_db()` to bind to primary when `DATABASE_REPLICA_URL` is not configured. Set it to `false` in production if missing replica configuration should fail startup.

## Replication Topology

Recommended production topology:

1. One writable PostgreSQL primary.
2. One or more asynchronous streaming read replicas.
3. Application servers connect to the primary for writes and to a read endpoint for replica-safe reads.
4. Migrations run only against the primary.
5. Backups are taken from managed snapshots or a replica, not from application traffic paths.

Read replicas must be treated as eventually consistent. Any flow that creates data and immediately needs to read it should use `get_write_db()` until the data is allowed to become eventually consistent.

## Failover Strategy

Primary failure:

1. Promote a healthy replica to primary using the database provider's managed failover process.
2. Update `DATABASE_PRIMARY_URL` to the promoted primary endpoint, or use a stable provider-managed writer endpoint.
3. Restart server and worker processes so SQLAlchemy engines reconnect to the new writer.
4. Point `DATABASE_REPLICA_URL` at a healthy replica after the new replica is attached.
5. Run a smoke test: auth login, chat session creation, WebSocket message, history retrieval.

Replica failure or high lag:

1. Set `DATABASE_READ_FROM_REPLICA=false`.
2. Restart server processes to route `get_read_db()` to primary.
3. Repair or replace the replica.
4. Re-enable replica reads once lag is healthy and history reads are correct.

Operational checks to add before production:

- Monitor replica lag.
- Alert when read errors increase or when replica lag exceeds the app's tolerance.
- Document provider-specific promotion commands.
- Add CI or startup checks that production has both primary and replica URLs when fallback is disabled.
