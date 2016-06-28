import re
import tempfile
from collections import OrderedDict

from django.core.exceptions import FieldError
from django.db.models.sql import compiler

from .features import DatabaseFeatures


class SQLCompiler(compiler.SQLCompiler):
    _re_advanced_group_by = re.compile(r'GROUP BY(.*%s.*)((ORDER BY)|(LIMIT))?', re.MULTILINE)

    def as_sql(self, with_limits=True, with_col_aliases=False, subquery=False):
        sql, params = super(SQLCompiler, self).as_sql(with_limits, with_col_aliases, subquery)

        if self._re_advanced_group_by.search(sql) is not None:
            print "GROUP BY with parameters found: we need to rewrite the sql"

            # we need to rewrite queries that have parameters inside the GROUP BY clause, such as this one:
            #
            #   sql = """SELECT (first_seen >= %s), COUNT(*) FROM "TABLEAU_ALL" GROUP BY (first_seen >= %s)"""
            #   params = ['2016-05-04', '2016-05-04']
            #
            # to this
            #
            #   sql = """
            #       WITH tmp AS (SELECT %s as p0)
            #           SELECT(first_seen >= p0), COUNT(*)
            #           FROM "TABLEAU_ALL", tmp
            #           GROUP BY(first_seen >= p0)
            #   """
            #   params = ['2016-05-04']
            #

            # first, we generate a sequence of unique parameter names p0, p1... for each individual parameter
            param_names = map(lambda (i, p): 'p%d' % (i,), enumerate(params))
            named_params = OrderedDict()
            for i, (param_name, param_value) in enumerate(zip(param_names, params)):
                # for every parameter, find the first parameter in the list that has the same value
                param_names[i] = next(name for (name,value) in zip(param_names, params) if value==param_value)
                # for these repeated parameters, we will use the first name:
                # if a value appears twice (for instance p3 and p5 have the same value), we will use p3 in both places
                named_params[param_names[i]] = param_value
                # print i, param_name, param_value, param_names[i]

            # param_names has a list of replacements for each of the %s in the original query with the correct parameter name
            # named_params has an ordered dict of parameters with unique values

            # generate a unique temporary name
            tmp_name = '"TMP_%s"' % (next(tempfile._get_candidate_names()),)

            # generate the first part of the sql sentence: a %s placeholder for each named parameter
            with_sql = 'WITH {tmp_name} AS (SELECT {named_params})'.format(
                tmp_name=tmp_name,
                named_params=", ".join(map(lambda name: '%s AS {name}'.format(name=name), named_params.keys()))
            )

            # in the rest of sql sentence, replace %s placeholders with their corresponding parameter names
            for named_param in param_names:
                sql = sql.replace('%s', tmp_name + "." + named_param, 1)

            # combine the two sql parts into a single statement
            sql = with_sql + ' ' + sql.replace('FROM ', 'FROM {tmp_name}, '.format(tmp_name=tmp_name))

            # new param list contains only one item for each distinct parameter value
            params = named_params.values()

        return sql, params


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
