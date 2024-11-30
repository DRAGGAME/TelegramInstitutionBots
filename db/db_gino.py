import psycopg2
from psycopg2 import sql
from psycopg2 import Error

from config import ip, PG_user, DATABASE, PG_password
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Sqlbase:
    def __init__(self):
        self.connection = psycopg2.connect(host=ip, user=PG_user, password=PG_password, database=DATABASE)
        self.connection.autocommit=False
        self.cursor = self.connection.cursor()


    def spaltenerstellen(self):
        # Создание столбцов
        try:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS servers(
                            Id SERIAL PRIMARY KEY,
                            Data_times text,
                            Place text,
                            Id_user text,
                            Rating INTEGER,
                            Review text
                            );''')
            self.connection.commit()
        except Error as e:
            # Откат изменений в случае ошибки
            self.connection.rollback()
            # Выводим сообщение об ошибке и ее код
            print(f"Transaction failed: {e.pgcode} - {e.pgerror}")

        finally:
            if self.connection:
                self.cursor.close()
                self.connection.close()
                print('Всё окей')


    def spaltenausgabe(self):
        try:
            query = sql.SQL("SELECT {fields} FROM {table} WHERE {pkey} = %s;").format(
                    fields=sql.SQL(', ').join([
                        sql.Identifier('id'),
                        sql.Identifier('data_times'),
                        sql.Identifier('place'),
                        sql.Identifier('id_user'),
                        sql.Identifier('rating'),
                        sql.Identifier('review')
                    ]),
                    table=sql.Identifier('servers'),
                    pkey=sql.Identifier('id')
                )
            self.cursor.execute(query, (1,))
            self.connection.commit()
            print(self.cursor.fetchone())
        except Error as e:
            # Откат изменений в случае ошибки
            self.connection.rollback()
            # Выводим сообщение об ошибке и ее код
            print(f"Transaction failed: {e.pgcode} - {e.pgerror}")

        finally:
            if self.connection:
                self.cursor.close()
                self.connection.close()
                print('Всё окей')

    def ins(self, time, place, user, rating, review):
        try:
            self.cursor.execute("INSERT INTO servers (Data_times, Place, Id_user, Rating, Review) VALUES (%s, %s, %s, %s, %s);", (time, place, user, rating, review))
            self.connection.commit()
        except Error as e:
            # Откат изменений в случае ошибки
            self.connection.rollback()
            # Выводим сообщение об ошибке и ее код
            print(f"Transaction failed: {str(e)}")

        # finally:
        #     if self.connection:
        #         self.cursor.close()
        #         self.connection.close()
        #         print('Всё окей')

    def delete(self):
        try:
            self.cursor.execute("DROP TABLE servers;")
            self.connection.commit()

        except Error as e:
            # Откат изменений в случае ошибки
            self.connection.rollback()
            # Выводим сообщение об ошибке и ее код
            print(f"Transaction failed: {str(e)}")

        finally:
            if self.connection:
                self.cursor.close()
                self.connection.close()
                print('Всё круто')
if __name__ == '__main__':

    test_sql_class = Sqlbase()

    test_sql_class.spaltenausgabe()
