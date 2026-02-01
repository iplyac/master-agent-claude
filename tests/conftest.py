"""Shared test fixtures and mock setup."""

import sys
from unittest.mock import MagicMock

# Mock google.cloud.firestore before any imports
# This must happen before any module imports conversation_store or app
mock_firestore = MagicMock()
mock_google_cloud = MagicMock()
mock_google_cloud.firestore = mock_firestore
sys.modules["google.cloud"] = mock_google_cloud
sys.modules["google.cloud.firestore"] = mock_firestore
sys.modules["google.cloud.firestore_v1"] = MagicMock()
sys.modules["google.cloud.firestore_v1.base_document"] = MagicMock()

# Export for use in tests
__all__ = ["mock_firestore", "mock_google_cloud"]
