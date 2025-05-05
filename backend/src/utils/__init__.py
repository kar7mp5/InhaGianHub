from os.path import dirname
from sys import path

path.insert(0, dirname(__file__))

from .config_loader import load_facility_config 