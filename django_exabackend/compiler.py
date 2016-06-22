from django.db.models.sql import compiler

from .features import DatabaseFeatures

class SQLCompiler(compiler.SQLCompiler):
    pass

class SQLInsertCompiler(compiler.SQLInsertCompiler, SQLCompiler):
    def prepare_value(self, field, value):
        value = super(SQLInsertCompiler, self).prepare_value(field, value)
        itype = field.get_internal_type()
        if itype == 'DateTimeField':
            # cut out the timezone
            try:
                ma_date_tz = DatabaseFeatures.datetime_tz_cut.match(value)
                if ma_date_tz:
                    value = ma_date_tz.group(1)
            except: pass
        return value

    def field_as_sql(self, field, val):
        if field is None: sql, params = val, []
        elif hasattr(val, 'as_sql'): sql, params = self.compile(val)
        elif hasattr(field, 'get_placeholder'):
            sql, params = field.get_placeholder(val, self, self.connection), [val]
        else: sql, params = '?', [val]
        itype = field.get_internal_type()
        return sql, params

class SQLDeleteCompiler(compiler.SQLDeleteCompiler, SQLCompiler):
    pass

class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    def as_sql(self):
        self.pre_sql_setup()
        if not self.query.values:
            return '', ()
        qn = self.quote_name_unless_alias
        values, update_params = [], []
        for field, model, val in self.query.values:
            if hasattr(val, 'resolve_expression'):
                val = val.resolve_expression(self.query, allow_joins=False, for_save=True)
                if val.contains_aggregate:
                    raise FieldError("Aggregate functions are not allowed in this query")
            elif hasattr(val, 'prepare_database_save'):
                if field.remote_field:
                    val = field.get_db_prep_save(val.prepare_database_save(field), connection=self.connection)
                else: raise TypeError(
                        "Tried to update field %s with a model instance, %r. "
                        "Use a value compatible with %s."
                        % (field, val, field.__class__.__name__))
            else: val = field.get_db_prep_save(val, connection=self.connection)
            if hasattr(field, 'get_placeholder'):
                placeholder = field.get_placeholder(val, self, self.connection)
            else: placeholder = '?'
            name = field.column
            if hasattr(val, 'as_sql'):
                sql, params = self.compile(val)
                values.append('%s = %s' % (qn(name), sql))
                update_params.extend(params)
            elif val is not None:
                values.append('%s = %s' % (qn(name), placeholder))
                update_params.append(val)
            else: values.append('%s = NULL' % qn(name))
        if not values:
            return '', ()
        table = self.query.tables[0]
        result = ['UPDATE %s SET' % qn(table), ', '.join(values)]
        where, params = self.compile(self.query.where)
        if where: result.append('WHERE %s' % where)
        return ' '.join(result), tuple(update_params + params)

class SQLAggregateCompiler(compiler.SQLAggregateCompiler, SQLCompiler):
    pass
