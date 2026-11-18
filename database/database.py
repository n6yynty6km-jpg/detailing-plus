
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Если DATABASE_URL задан, подключаемся к Neon.
# Если нет — используем локальную PostgreSQL.
database_url = os.getenv("DATABASE_URL")
print("DATABASE_URL найдена:", bool(database_url))
print("DATABASE_URL начинается с postgresql://:", database_url.startswith("postgresql://") if database_url else False)
if database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

if database_url:
    engine = create_engine(
        database_url,
        connect_args={"options": "-c client_encoding=UTF8"},
        pool_pre_ping=True,
    )
else:
    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )

    engine = create_engine(
        connection_url,
        connect_args={"options": "-c client_encoding=UTF8"},
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
