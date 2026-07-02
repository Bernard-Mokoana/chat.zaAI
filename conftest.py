import os


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_PRIMARY_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("DATABASE_REPLICA_URL", "")
os.environ.setdefault("DATABASE_READ_FROM_REPLICA", "false")
os.environ.setdefault("DATABASE_ALLOW_REPLICA_FALLBACK", "true")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("EXPIRES_IN", "60")
os.environ.setdefault("REFRESH_JWT_SECRET", "test-refresh-jwt-secret")
os.environ.setdefault("VERIFY_JWT_SECRET", "test-verify-jwt-secret")
