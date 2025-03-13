# Copyright (c) Microsoft. All rights reserved.

from dotenv import load_dotenv

from . import config

# Load environment variables from .env into the settings object.
load_dotenv()
settings = config.Settings()
