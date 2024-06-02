import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.core import app
import example

celery = app
