import asyncpg
import os

'''Для работы с .env'''

# from dotenv import load_dotenv

# load_dotenv = load_dotenv()

database = os.getenv('DATABASE')

user = os.getenv('PG_user')
password = os.getenv('PG_password')
ip = os.getenv('ip')


class Sqlbase:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=ip,
                user=user,
                password=password,
                database=database,
                min_size=1,
                max_size=10000
            )
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            raise

    async def close(self):
        if self.pool:
            await self.pool.close()


    async def execute_query(self, query, params=None):
        if not self.pool:
            raise ValueError("Пул соединений не создан. Убедитесь, что вызвали connect().")
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    if params:
                        return await connection.fetch(query, *params)
                    return await connection.fetch(query)
        except asyncpg.PostgresError as e:
            print(f"Ошибка выполнения запроса: {e}")
            raise

    async def spaltenerstellen(self):
        query = '''
            CREATE TABLE IF NOT EXISTS servers (
                Id SERIAL PRIMARY KEY,
                data_times TIMESTAMP,
                address TEXT,
                place TEXT,
                id_user TEXT,
                rating INT,
                review TEXT
            );
        '''
        await self.execute_query(query)

    async def ins(self, data_times, address, place, id_user, rating, review):
        query = '''
            INSERT INTO servers (data_times, address, place, id_user, rating, review)
            VALUES ($1, $2, $3, $4, $5, $6);
        '''
        await self.execute_query(query, (data_times, address, place, id_user, rating, review))

    async def ins_ins(self, data_times,  place, id_user, rating, review):
        query = '''
            INSERT INTO servers (data_times, place, id_user, rating, review)
            VALUES ($1, $2, $3, $4, $5);
        '''
        await self.execute_query(query, (data_times, place, id_user, rating, review))
    async def delete(self):
        query = "DROP TABLE IF EXISTS servers;"
        await self.execute_query(query)



