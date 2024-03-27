from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./sql_app.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=True
)

async_session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Files(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str]
    number_word: Mapped[int]


class FilesBase(BaseModel):
    file_path: str
    number_word: int


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def add_file_to_db(session, files_data):
    files = Files(**files_data.dict())
    session.add(files)
    await session.commit()


async def get_file_from_db(session: AsyncSession):

    files = await session.execute(
        select(Files)
    )

    return files.scalars().all()


