from time import sleep

import psycopg2
from psycopg2.extensions import QueryCanceledError
from log_files import info
from constants import start_dir
from settings import DB_POLIGON_HOST, DB_POLIGON_PORT, DB_POLIGON_NAME, DB_POLIGON_USER, DB_POLIGON_PASSWD


class ConnectionManager:
    def __init__(
            self, ip=DB_POLIGON_HOST, port=DB_POLIGON_PORT, db_name=DB_POLIGON_NAME,
            user=DB_POLIGON_USER, password=DB_POLIGON_PASSWD, timeout=60
    ):
        self.__ip = ip
        self.__port = port
        self.__db_name = db_name
        self.__user = user
        self.__password = password
        self.__timeout = timeout
        self.__create_partition = "CREATE TABLE {table_partition} PARTITION OF {table} FOR " \
                                  "VALUES FROM {condition};"
        self.__reate_table_section_comment = "COMMENT ON TABLE  {TABLE_SECTION} " \
                                             "IS '{COMMENT}';"

        self.__check_table = "SELECT to_regclass('{table_partition}');"

        self.__insert = "INSERT INTO {table} ({parameter}) VALUES {values};"

        self.__request = "SELECT {parameter} FROM {tabel}{condition}{group}{group_having}{order};"

        self.__update = "UPDATE {table} SET {values} {conditions};"

        self.__connection = None
        self.__cursor = None
        self.result = None
        self.result_err = None
        self.__connect()

    def __connect(self):
        while True:
            try:
                self.__connection = psycopg2.connect(
                    database=self.__db_name, host=self.__ip, port=self.__port, user=self.__user,
                    password=self.__password, connect_timeout=self.__timeout,
                    options='-c statement_timeout={timeout}'.format(timeout=self.__timeout * 1000)
                )
                self.result_err = 'ok'
                info(f'Выполнено подключение к базе данных "{self.__db_name}" host "{self.__ip}".', start_dir)
                self.__cursor = self.__connection.cursor()
                break
            except (Exception, psycopg2.Error) as error:
                self.result_err = f'PostgreSQL error: {error}.'
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                sleep(10)
            except psycopg2.OperationalError as error:
                self.result_err = 'connection timeout'
                info(f'Ошибка при подключении к базе "{self.__db_name}", host "{self.__ip}": {error}', start_dir)
                sleep(10)

    def disconnect(self):
        if self.__cursor:
            self.__cursor.close()
        if self.__connection:
            self.__connection.close()
            info(f'Выполнено отключение от базы данных "{self.__db_name}" host "{self.__ip}".', start_dir)

    def create_tables_partition(self, scheme_data, section, condition, comment=None, permissions=None):
        n = 0
        while True:
            self.result = None
            table_partition = f'{scheme_data}'
            table_partition_parent = table_partition
            partition = section[-1]
            for k in section:
                table_partition_parent = table_partition
                if table_partition != scheme_data:
                    # table_partition += '.'
                    table_partition += f'_{k}'
                else:
                    table_partition += '.'
                    table_partition += f'{k}'

            sql_add_tabel = self.__check_table.format(table_partition=table_partition)

            try:
                self.__cursor.execute(sql_add_tabel)
                self.result = self.__cursor.fetchone()
                if self.result[0]:

                    self.result = table_partition
                else:
                    sql_add_tabel = self.__create_partition.format(
                        table_partition=table_partition, table=table_partition_parent,
                        condition=condition
                    )
                    self.result = ''

                    self.__cursor.execute(sql_add_tabel)
                    self.result = self.__connection.commit()
                    self.result = partition
                    self.result_err = 'ok'
                    info(f'Создана секция таблицы "{table_partition}".', start_dir)
                    if comment:
                        sql_comment_table = self.__reate_table_section_comment.format(TABLE_SECTION=table_partition,
                                                                                      COMMENT=comment)
                        self.__cursor.execute(sql_comment_table)
                        info(f'Добавлен коментарий к секции таблицы "{table_partition}".', start_dir)
                    if permissions:
                        self.__cursor.execute(permissions)
                break
            except (Exception, psycopg2.Error) as error:
                n += 1
                self.__connection.commit()
                self.result_err = f'PostgreSQL error: {error}.'
                self.result = f"Ошибка при работе с PostgreSQL: {error}."
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                if n == 5:
                    self.result = 'error'
                    break

                sleep(1/2)
                self.__connect()
            except QueryCanceledError as error:
                self.disconnect()
                self.result_err = 'connection timeout'
                self.result = f"Ошибка при работе с PostgreSQL: {error}"
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                sleep(1)
                self.__connect()

    def inserts(self, scheme_data, section, parameter, values, description=None):
        n = 0
        while True:
            table_partition = f'{scheme_data}'
            for k in section:
                if table_partition != scheme_data:
                    table_partition += f'_{k}'
                else:
                    table_partition += '.'
                    table_partition += f'{k}'
            insert = self.__insert.format(
                table=table_partition, parameter=parameter, values=values)
            # print(insert)
            try:
                self.__cursor.execute(insert)
                self.result = self.__connection.commit()
                self.result_err = 'ok'
                if description:
                    info(f'Добавлены в таблицу {table_partition} за "{description}".', start_dir)
                break
            except (Exception, psycopg2.Error) as error:
                if 'повторяющееся значение ключа нарушает ограничение уникальности' in str(error):
                    self.__connection.commit()
                    info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                    break
                n += 1
                self.__connection.commit()
                self.result_err = f'PostgreSQL error: {error}.'
                self.result = f"Ошибка при работе с PostgreSQL: {error}"
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                if n == 5:
                    break
                sleep(1/2)
            except QueryCanceledError as error:
                self.disconnect()
                self.result_err = 'connection timeout'
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                sleep(1)
                self.__connect()

    def requests(self, parameter, tabel, condition='', group='', group_having='', order='', x=3000):
        n = 0

        if condition:
            condition = f' WHERE {condition}'
        if group:
            group = f' group by {group}'
        if group_having:
            group_having = f' having {group_having}'
        if order:
            order = f' order by {order}'
        while True:
            self.result = ''
            request = self.__request.format(
                parameter=parameter, tabel=tabel, condition=condition,
                group=group, group_having=group_having, order=order
            )
            try:
                # print(request)
                self.__cursor.execute(request)
                self.result = self.__cursor.fetchmany(x)
                self.result_err = 'ok'
                break
            except (Exception, psycopg2.Error) as error:
                n += 1
                self.__connection.commit()
                self.result_err = f'PostgreSQL error: {error}.'
                self.result = f"Ошибка при работе с PostgreSQL: {error}"
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                if n == 10:
                    break
                sleep(1)
            except QueryCanceledError as error:
                self.disconnect()
                self.result_err = 'connection timeout'
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                sleep(1)
                self.__connect()

    def update(self, table, values, conditions=''):
        while True:
            self.result = ''
            update = self.__update.format(table=table, values=values, conditions=conditions)
            try:
                # print(update)
                self.__cursor.execute(update)
                self.result = self.__connection.commit()
                self.result_err = 'ok'
                info(f'Обновлены в таблице {table}, данные "{values}", по условию: "{conditions[6:]}".', start_dir)
                break
            except (Exception, psycopg2.Error) as error:
                self.__connection.commit()
                self.result_err = f'PostgreSQL error: {error}.'
                self.result = f"Ошибка при работе с PostgreSQL: {error}"
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)

            except QueryCanceledError as error:
                self.disconnect()
                self.result_err = 'connection timeout'
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                sleep(1)
                self.__connect()
