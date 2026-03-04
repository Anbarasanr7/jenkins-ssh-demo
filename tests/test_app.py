import os
from app import add

def test_add():
    assert add(2, 3) == 5

def test_optional_failure():
    # Set FORCE_FAIL=true in pipeline params to simulate failing build
    assert os.getenv("FORCE_FAIL", "false").lower() != "true"
