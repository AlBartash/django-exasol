import re
from django.db.backends.base.features import BaseDatabaseFeatures
from django.utils.functional import cached_property

from .base import Database

try: import pytz
except ImportError: pytz = None

class DatabaseFeatures(BaseDatabaseFeatures):
    datetime_tz_cut = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[.]\d{6})[-+]\d{2}:\d{2}$')
