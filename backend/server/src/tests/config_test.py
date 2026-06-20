import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from backend.server.main import api

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    return db

@pytest.fixture
def client():
    return TestClient(api)