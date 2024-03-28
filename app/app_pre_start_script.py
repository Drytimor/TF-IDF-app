import db
import asyncio


async def init_db():
    async with db.engine.begin() as conn:
        await conn.run_sync(db.Base.metadata.drop_all)
        await conn.run_sync(db.Base.metadata.create_all)



if __name__ == "__main__":
    asyncio.run(init_db())
