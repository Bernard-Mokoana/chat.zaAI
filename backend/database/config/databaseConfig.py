import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

load_dotenv()

PRIMARY_URL = os.environ.get("DATABASE_PRIMARY_URL")
REPLICA_URL = os.environ.get("DATABASE_REPLICA_URL")
READ_FROM_REPLICA = os.environ.get("DATABASE_READ_FROM_REPLICA", "true").strip().lower() == "true"
ALLOW_REPLICA_FALLBACK = os.environ.get("DATABASE_ALLOW_REPLICA_FALLBACK", "true").strip().lower() == "true"

if not PRIMARY_URL:
    raise ValueError("DATABASE_PRIMARY_URL environment variable must be set.")

if READ_FROM_REPLICA and not REPLICA_URL and not ALLOW_REPLICA_FALLBACK:
    raise ValueError(
        "DATABASE_REPLICA_URL must be set when DATABASE_READ_FROM_REPLICA=true "
        "and DATABASE_ALLOW_REPLICA_FALLBACK=false."
    )

engine_primary = create_engine(PRIMARY_URL, pool_pre_ping=True)
engine_replica = create_engine(REPLICA_URL, pool_pre_ping=True) if REPLICA_URL else engine_primary

read_engine = engine_replica if READ_FROM_REPLICA and REPLICA_URL else engine_primary

SessionPrimary = sessionmaker(autocommit=False, autoflush=False, bind=engine_primary) 
SessionReplica = sessionmaker(autocommit=False, autoflush=False, bind=read_engine)

class Base(DeclarativeBase):
    pass

def get_write_db():
    db = SessionPrimary()
    try:
        yield db
    # Session rollback on exception
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_read_db():
    db = SessionReplica()
    try:
        yield db
    # Session rollback on exception
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
