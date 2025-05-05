from os.path import dirname
from sys import path

path.insert(0, dirname(__file__))

from .crawling_service import crawl_facility_reservations