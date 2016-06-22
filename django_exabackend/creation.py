import subprocess
import sys

from django.db.backends.base.creation import BaseDatabaseCreation

from .client import DatabaseClient

class DatabaseCreation(BaseDatabaseCreation):
    pass
