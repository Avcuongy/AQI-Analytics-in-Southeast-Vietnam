import datetime
import logging
import sys
import time
import json
from pathlib import Path

import pandas as pd
import requests
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "historical"