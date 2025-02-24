import os
import sys

# Add the vendor directory to sys.path so that packages like pydantic can be imported
vendor_path = os.path.join(os.path.dirname(__file__), 'vendor')
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)
    