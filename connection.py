from time import sleep

import psycopg2
from psycopg2.extensions import QueryCanceledError
from log_files import info
from constants import start_dir
import datetime
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
                                  "VALUES FROM ('{date_from} 00:00:00') TO ('{date_to} 00:00:00');"

        self.__check_table = "SELECT to_regclass('{table_partition}');"

        self.__insert = "INSERT INTO {table} ({parameter}) VALUES {values};"

        self.__request = "SELECT {parameter} FROM {tabel} WHERE {condition};"

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

    def create_tables(self, table, date):
        while True:
            date_to = date + datetime.timedelta(days=1)
            table_partition = f'{table}_{date.strftime("%Y_%m_%d")}'
            sql_add_tabel = self.__check_table.format(table_partition=table_partition)
            try:
                self.__cursor.execute(sql_add_tabel)
                self.result = self.__cursor.fetchone()
                if self.result[0]:

                    self.result = date.strftime("%Y-%m-%d")
                else:
                    sql_add_tabel = self.__create_partition.format(
                        table_partition=table_partition, table=table,
                        date_from=date.strftime('%Y-%m-%d'), date_to=date_to.strftime('%Y-%m-%d')
                    )
                    self.result = ''

                    self.__cursor.execute(sql_add_tabel)
                    self.result = self.__connection.commit()
                    self.result = date.strftime("%Y-%m-%d")
                    self.result_err = 'ok'
                    info(f'Создана секция таблицы "{table_partition}".', start_dir)
                break
            except (Exception, psycopg2.Error) as error:
                self.__connection.commit()
                self.result_err = f'PostgreSQL error: {error}.'
                self.result = f"Ошибка при работе с PostgreSQL: {error}."
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                sleep(1)
                self.__connect()
            except QueryCanceledError as error:
                self.disconnect()
                self.result_err = 'connection timeout'
                self.result = f"Ошибка при работе с PostgreSQL: {error}"
                info(f"Ошибка при работе с PostgreSQL: {error}", start_dir)
                sleep(1)
                self.__connect()

    def inserts(self, table, parameter, values):
        while True:
            insert = self.__insert.format(
                table=table, parameter=parameter, values=values)
            # print(insert)
            try:
                self.__cursor.execute(insert)
                self.result = self.__connection.commit()
                self.result_err = 'ok'
                info(f'Добавлены в таблицу {table}, данные "{values}".', start_dir)
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

    def requests(self, parameter, tabel, condition, x=3000):
        while True:
            self.result = ''
            request = self.__request.format(parameter=parameter, tabel=tabel, condition=condition)
            try:
                # print(request)
                self.__cursor.execute(request)
                self.result = self.__cursor.fetchmany(x)
                self.result_err = 'ok'
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
