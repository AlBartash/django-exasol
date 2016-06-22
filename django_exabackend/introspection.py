from collections import namedtuple
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.introspection import (
    BaseDatabaseIntrospection, FieldInfo, TableInfo,
)

class DatabaseIntrospection(BaseDatabaseIntrospection):
    def get_table_list(self, cursor):
        cursor.execute('SELECT TABLE_NAME, TABLE_TYPE FROM CAT')
        rows = cursor.fetchall()
        tablelist = []
        for r in rows:
            if r[1] == 'TABLE':
                tablelist.append(TableInfo(r[0], 't'))
            elif r[1] == 'VIEW':
                tablelist.append(TableInfo(r[0], 'v'))
        #print "@@@ get_table_list", repr(rows), repr(tablelist)
        return tablelist
