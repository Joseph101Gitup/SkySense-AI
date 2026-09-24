"""
Root Test Suite for SKYsense AI.
Configures Django environment and exposes all 13 automated test suites.
"""

import os
import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "05_Backend"
AI_MODEL_DIR = PROJECT_ROOT / "03_AI_Model"

for p in [str(BACKEND_DIR), str(AI_MODEL_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skysense.settings")
import django
django.setup()

# Expose all test modules for unittest/pytest discovery
from tests.test_01_django_app_loads import DjangoApplicationLoadTests
from tests.test_02_home_page import HomePageTests
from tests.test_03_login import LoginTests
from tests.test_04_registration import RegistrationTests
from tests.test_05_auth_protection import AuthenticationProtectionTests
from tests.test_06_prediction_model import PredictionModelTests
from tests.test_07_image_upload_validation import ImageUploadValidationTests
from tests.test_08_ai_inference import AIInferenceTests
from tests.test_09_prediction_database_creation import PredictionDatabaseCreationTests
from tests.test_10_prediction_history import PredictionHistoryTests
from tests.test_11_api_endpoint import ApiEndpointTests
from tests.test_12_invalid_image_handling import InvalidImageHandlingTests
from tests.test_13_unsupported_file_handling import UnsupportedFileHandlingTests

__all__ = [
    "DjangoApplicationLoadTests",
    "HomePageTests",
    "LoginTests",
    "RegistrationTests",
    "AuthenticationProtectionTests",
    "PredictionModelTests",
    "ImageUploadValidationTests",
    "AIInferenceTests",
    "PredictionDatabaseCreationTests",
    "PredictionHistoryTests",
    "ApiEndpointTests",
    "InvalidImageHandlingTests",
    "UnsupportedFileHandlingTests",
]
