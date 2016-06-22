from django.core import checks
from django.db.backends.base.validation import BaseDatabaseValidation
from django.utils.version import get_docs_version

class DatabaseValidation(BaseDatabaseValidation):
    pass
