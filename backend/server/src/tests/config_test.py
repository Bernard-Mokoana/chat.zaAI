from unittest.mock import MagicMock

import pytest
from backend.server.main import api
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def client():
    return TestClient(api)
