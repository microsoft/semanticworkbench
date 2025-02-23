# import os
# import sys

# # Add the vendor directory to sys.path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vendor')))

from . import config  # Ensure relative imports for Fusion Add-In compatibility
settings = config.Settings()
