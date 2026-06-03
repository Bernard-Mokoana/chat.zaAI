import os
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.exc import OperationalError

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

def get_resilient_engine(url, max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                return engine
        except OperationalError:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)

engine_primary = get_resilient_engine(PRIMARY_URL)

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
