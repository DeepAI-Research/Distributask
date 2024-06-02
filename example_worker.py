import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.distributaur import Distributaur

from example import *

if __name__ == "__main__":
    distributaur = Distributaur()
    celery = distributaur.app
