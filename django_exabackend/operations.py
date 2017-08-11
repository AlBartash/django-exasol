from __future__ import unicode_literals

import uuid, re

from django.conf import settings
from django.db.backends.base.operations import BaseDatabaseOperations
from django.utils import six, timezone
from django.utils.encoding import force_text


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django_exabackend.compiler"

    def convert_datetimefield_value(self, value, expression, connection, context):
        #print "@@@ convert_datetimefield_value", repr((value, expression, connection, context))
        if value is not None:
            if not isinstance(value, datetime.datetime):
                value = parse_datetime(value)
            value = value.strftime('%Y-%m-%d %H:%M:%S.%f')
        return value

    def quote_name(self, name):
        """
        Returns a quoted version of the given table, index or column name. Does
        not quote the given name if it's already been quoted.
        Supports schema.table form identifiers -> "schema"."table"
        """
        if name.startswith('"') and name.endswith('"'):
            return name # Quoting once is enough.
        return '.'.join(['%s%s%s' % ('"', piece.upper(), '"') for piece in name.split('.')])
#        return '.'.join(['%s%s%s' % ('"', piece, '"') for piece in name.split('.')])

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

    def lookup_cast(self, lookup_type, internal_type=None):
        if lookup_type in ('iexact', 'icontains', 'istartswith', 'iendswith'):
            return "UPPER(%s)"
        return "%s"

    def last_insert_id(self, cursor, table_name, pk_name):
        table_name = self.quote_name(table_name)
        cursor.execute("SELECT COLUMN_IDENTITY FROM EXA_ALL_COLUMNS WHERE '\"'||COLUMN_SCHEMA||'\".\"'||COLUMN_TABLE||'\"'='"+table_name+"' AND COLUMN_IDENTITY IS NOT NULL")
        return cursor.fetchone()[0]

