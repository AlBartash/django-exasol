from __future__ import unicode_literals

import uuid, re

from django.conf import settings
from django.db.backends.base.operations import BaseDatabaseOperations
from django.utils import six, timezone
from django.utils.encoding import force_text


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django.db.backends.exasol.compiler"

    def convert_datetimefield_value(self, value, expression, connection, context):
        #print "@@@ convert_datetimefield_value", repr((value, expression, connection, context))
        if value is not None:
            if not isinstance(value, datetime.datetime):
                value = parse_datetime(value)
            value = value.strftime('%Y-%m-%d %H:%M:%S.%f')
        return value

    def quote_name(self, name):
        return '"%s"' % name.replace('"', '""')

    def bulk_insert_sql(self, fields, placeholder_rows):
        #print "@@@ bulk_insert_sql", repr(fields), repr(placeholder_rows)
        placeholder_rows_sql = (", ".join(row) for row in placeholder_rows)
        values_sql = ", ".join("(%s)" % sql for sql in placeholder_rows_sql)
        return "VALUES " + values_sql

    def get_db_converters(self, expression):
        #print "@@@ get_db_converters", repr(expression)
        converters = super(DatabaseOperations, self).get_db_converters(expression)
        internal_type = expression.output_field.get_internal_type()
        if internal_type == 'DateTimeField':
            converters.append(self.convert_datetimefield_value)
        return converters

    def last_insert_id(self, cursor, table_name, pk_name):
        return 0

