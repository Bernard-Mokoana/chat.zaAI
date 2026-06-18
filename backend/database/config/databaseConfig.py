import os
import time
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.exc import OperationalError

load_dotenv()

logger = logging.getLogger(__name__)

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

def get_resilient_engine(url, max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                logger.info(f"Database connection established on attempt {attempt + 1}")
                return engine
        except OperationalError as e:
            logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                logger.error(f"Database connection failed after {max_retries} attempts")
                raise
            time.sleep(delay)

engine_primary = get_resilient_engine(PRIMARY_URL)
engine_replica = get_resilient_engine(REPLICA_URL) if REPLICA_URL else engine_primary

read_engine = engine_replica if READ_FROM_REPLICA and REPLICA_URL else engine_primary

sessionPrimary = sessionmaker(autocommit=False, autoflush=False, bind=engine_primary)
sessionReplica = sessionmaker(autocommit=False, autoflush=False, bind=read_engine)
class Base(DeclarativeBase):
    pass

def get_write_db():
    db = sessionPrimary()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_read_db():
    db = sessionReplica()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
