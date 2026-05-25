import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

PRIMARY_URL = os.environ.get("DATABASE_PRIMARY_URL")
REPLICA_URL = os.environ.get("DATABASE_REPLICA_URL")

if not PRIMARY_URL or not REPLICA_URL:
    raise ValueError("Both DATABASE_PRIMARY_URL and DATABASE_REPLICA_URL environment variables must be set.")

engine_primary = create_engine(PRIMARY_URL, pool_pre_ping=True)
engine_replica = create_engine(REPLICA_URL, pool_pre_ping=True)

SessionPrimary = sessionmaker(autocommit=False, autoflush=False, bind=engine_primary) 
SessionReplica = sessionmaker(autocommit=False, autoflush=False, bind=engine_replica)

Base = declarative_base()

def get_write_db():
    db = SessionPrimary()
    try:
        yield db
    finally:
        db.close()

def get_read_db():
    db = SessionReplica()
    try:
        yield db
    finally:
        db.close()