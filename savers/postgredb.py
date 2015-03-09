# coding: utf-8
from psycopg2._psycopg import ProgrammingError, InternalError
import psycopg2
from psycopg2.extras import DictCursor

from savers import Saver, IWriter

__author__ = 'morose'


class PostgreWriteError(Exception):
    pass


class Postgre(IWriter):
    u"""Postgresql db saver"""

    def __init__(self, table_name, saving_columns, **init_params):
        assert isinstance(saving_columns, (list, tuple)) and saving_columns
        self.saving_columns = saving_columns
        self.table_name = table_name
        db_value_template = '%({col})s'
        col_repr = [db_value_template.format(col=c) for c in saving_columns]

        self._insert_cmd = """INSERT INTO {table_name} ({cols}) VALUES ({pl_hld});""".format(
            table_name=table_name,
            cols=', '.join(saving_columns),
            pl_hld=', '.join(col_repr),
        )

        self.connector = psycopg2.connect(
            database=init_params.get('database'),
            user=init_params.get('user'),
            host=init_params.get('host'),
            password=init_params.get('password'),
        )
        self.cursor = self.connector.cursor(cursor_factory=DictCursor)

        self._create_table(table_name, saving_columns)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connector.commit()

        self.cursor.close()
        self.connector.close()

    def write_data(self, data):
        self.write_all(data)

    def write(self, row):
        self.cursor.execute(self._insert_cmd, row)

    def write_all(self, rows):
        self.cursor.executemany(self._insert_cmd, rows)

    def _create_table(self, table_name, columns=None):
        cols = ''
        if columns:
            cols = ', '.join([
                '{c_name} character varying(30)'.format(c_name=c_name)
                for c_name in columns if c_name.strip()
            ])
        create_table_sql = """\
        CREATE TABLE {t_name} \
        (id bigserial NOT NULL,\
        CONSTRAINT {t_name}_pkey PRIMARY KEY (id),
        {cols}\
        )\
        """.format(t_name=table_name, cols=cols)
        try:
            self.cursor.execute(create_table_sql)
        except ProgrammingError:
            self.connector.rollback()
            # probably table exist
            return False

        return True


class PostgreSaver(Saver):
    writer = Postgre
