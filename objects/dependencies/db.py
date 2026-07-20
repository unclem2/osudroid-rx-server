from objects.db import sessionmaker


async def get_db_session():
    async with sessionmaker() as session:
        yield session
