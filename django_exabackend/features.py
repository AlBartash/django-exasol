import re
from django.db.backends.base.features import BaseDatabaseFeatures
from django.utils.functional import cached_property

from django_exabackend.base import Database

try: import pytz
except ImportError: pytz = None


class DatabaseFeatures(BaseDatabaseFeatures):
    interprets_empty_strings_as_nulls = True
    has_case_insensitive_like = False
    can_introspect_binary_field = False
    datetime_tz_cut = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[.]\d{6})[-+]\d{2}:\d{2}$')

    def supports_transactions(self):
        return True
