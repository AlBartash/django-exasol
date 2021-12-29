"""
EXASOL database backend for Django.
"""
from __future__ import unicode_literals

import datetime
import re
import sys
import warnings

from django.conf import settings
from django.db import utils
from django.db.backends import utils as backend_utils
from django.db.backends.base.base import BaseDatabaseWrapper
from django.utils import six, timezone
#from django.utils.deprecation import RemovedInDjango20Warning
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.safestring import SafeBytes, SafeText

from django_pyodbc.compat import binary_type, text_type, timezone

try:
    import pyodbc as Database
except ImportError as e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading PyODBC module: %s" % e)

from .client import DatabaseClient
from .creation import DatabaseCreation
from .features import DatabaseFeatures
from .introspection import DatabaseIntrospection
from .operations import DatabaseOperations
from .schema import DatabaseSchemaEditor
from .validation import DatabaseValidation

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError

class CursorWrapper(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, args=None):
        try:
            query = self._format_query(query)
            if args is None:
                return self.cursor.execute(query)
            args = self._format_args(args)
            return self.cursor.execute(query, args)
        except Database.OperationalError as e:
            if e.args[0] in self.codes_for_integrityerror:
                six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
            raise

    def executemany(self, query, args):
        try:
            query = self._format_query(query)
            args = self._format_args(args)
            return self.cursor.executemany(query, args)
        except Database.OperationalError as e:
            if e.args[0] in self.codes_for_integrityerror:
                six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
            raise

    def _format_query(self, query):
        return force_str(query.replace('%s', '?'))

    def _format_args(self, args):
        args = map(lambda a: a.encode('utf-8') if isinstance(a, text_type) else a, args)
        return tuple(args)

    def _format_results(self, row):
        fields = map(lambda field: field.decode('utf-8') if isinstance(field, binary_type) else field, row)
        return tuple(fields)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is not None:
            return self._format_results(row)
        return []

    def fetchmany(self, chunk):
        return [self._format_results(row) for row in self.cursor.fetchmany(chunk)]

    def fetchall(self):
        return [self._format_results(row) for row in self.cursor.fetchall()]

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # Ticket #17671 - Close instead of passing thru to avoid backend
        # specific behavior.
        self.close()


class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'exasol'

    Database = Database
    SchemaEditorClass = DatabaseSchemaEditor

    operators = {
        # Since '=' is used not only for string comparision there is no way
        # to make it case (in)sensitive. It will simply fallback to the
        # database collation.
        'exact': '= %s',
        'iexact': "= UPPER(%s)",
        'contains': "LIKE %s ESCAPE '\\'",
        'icontains': "LIKE UPPER(%s) ESCAPE '\\'",
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': "LIKE %s ESCAPE '\\'",
        'endswith': "LIKE %s ESCAPE '\\'",
        'istartswith': "LIKE UPPER(%s) ESCAPE '\\'",
        'iendswith': "LIKE UPPER(%s) ESCAPE '\\'",

        # TODO: remove, keep native T-SQL LIKE wildcards support
        # or use a "compatibility layer" and replace '*' with '%'
        # and '.' with '_'
        'regex': 'REGEXP_LIKE %s',
        'iregex': "REGEXP_LIKE '(?i)' || %s",
    }

    def __init__(self, *args, **kwargs):
        self.client_class = DatabaseClient
        self.creation_class = DatabaseCreation
        self.features_class = DatabaseFeatures
        self.introspection_class = DatabaseIntrospection
        self.ops_class = DatabaseOperations
        self.validation_class = DatabaseValidation

        BaseDatabaseWrapper.__init__(self, *args, **kwargs)

    def init_connection_state(self):
        pass

    @cached_property
    def data_types(self):
        return {
            'AutoField': 'integer IDENTITY',
            'BigAutoField': 'bigint IDENTITY',
            'BinaryField': 'varchar(%(max_legth)s)',
            'BooleanField': 'boolean',
            'CharField': 'varchar(%(max_length)s)',
            'CommaSeparatedIntegerField': 'varchar(%(max_length)s)',
            'DateField': 'date',
            'DateTimeField': 'timestamp',
            'DecimalField': 'decimal(%(max_digits)s, %(decimal_places)s)',
            'DurationField': 'integer',
            'FileField': 'varchar(%(max_length)s)',
            'FilePathField': 'varchar(%(max_length)s)',
            'FloatField': 'double precision',
            'IntegerField': 'integer',
            'BigIntegerField': 'integer',
            'IPAddressField': 'char(15)',
            'GenericIPAddressField': 'char(39)',
            'NullBooleanField': 'boolean',
            'OneToOneField': 'integer',
            'PositiveIntegerField': 'integer',
            'PositiveSmallIntegerField': 'integer',
            'SlugField': 'varchar(%(max_length)s)',
            'SmallIntegerField': 'integer',
            'TextField': 'varchar(2000000)',
            'TimeField': 'time',
            'UUIDField': 'char(32)',
        }

    def get_connection_params(self):
        kw = {}; conn_params = self.settings_dict
        if conn_params.get('DSN', '') != '': kw['DSN'] = conn_params['DSN']
        if conn_params.get('USER', '') != '': kw['UID'] = conn_params['USER']
        if conn_params.get('PASSWORD', '') != '': kw['PWD'] = conn_params['PASSWORD']
        if conn_params.get('DRIVER', '') != '': kw['DRIVER'] = '{%s}' % conn_params['DRIVER']
        if conn_params.get('EXAHOST', '') != '': kw['EXAHOST'] = conn_params['EXAHOST']
        if conn_params.get('SCHEMA', '') != '': kw['SCHEMA'] = conn_params['SCHEMA']
        if conn_params.get('CONNECTIONLCCTYPE', '') != '': kw['CONNECTIONLCCTYPE'] = conn_params['CONNECTIONLCCTYPE']
        if conn_params.get('HOST', '') != '':
            if 'EXAHOST' in conn_params:
                raise ImproperlyConfigured("Either specify HOST and PORT settings or EXAHOST in setup, but not both")
            conn_params['EXAHOST'] = '%s:%s' % (conn_params['HOST'], conn_params.get('PORT', '8563'))
        if conn_params.get('INTTYPESINRESULTSIFPOSSIBLE', 'n').lower() == 'y':
            kw['INTTYPESINRESULTSIFPOSSIBLE'] = 'y'
        return kw

    def get_new_connection(self, conn_params):
        conn = Database.connect(**conn_params)
        if 'SCHEMA' in conn_params:
            try: conn.execute('OPEN SCHEMA %s' % conn_params['SCHEMA'])
            except: conn.execute('CREATE SCHEMA %s' % conn_params['SCHEMA'])
        return conn

    def create_cursor(self, name=None):
        cursor = self.connection.cursor()
        return CursorWrapper(cursor)

    def _set_autocommit(self, autocommit):
        with self.wrap_database_errors:
            self.connection.autocommit = autocommit
