
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, select, func, text

from database.database import engine as neon_engine
from database.models import Service, Client, Appointment

load_dotenv()

# Подключение к исходной локальной базе
local_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

local_engine = create_engine(local_url)

# Таблицы переносим в порядке связей:
# сначала услуги и клиенты, затем заявки.
tables = [
    Service.__table__,
    Client.__table__,
    Appointment.__table__,
]

try:
    # Считываем данные из локальной базы
    source_data = {}

    with local_engine.connect() as source:
        for table in tables:
            rows = source.execute(
                select(table)
            ).mappings().all()

            source_data[table.name] = [
                dict(row) for row in rows
            ]

    # Проверяем, что целевые таблицы пустые
    with neon_engine.begin() as destination:

        for table in tables:
            count = destination.execute(
                select(func.count()).select_from(table)
            ).scalar_one()

            if count != 0:
                raise Exception(
                    f"Таблица {table.name} не пустая. "
                    "Перенос остановлен."
                )

        # Переносим данные с сохранением исходных ID
        for table in tables:
            rows = source_data[table.name]

            if rows:
                destination.execute(
                    table.insert(),
                    rows
                )

            print(
                f"{table.name}: перенесено {len(rows)} записей"
            )

        # Синхронизируем последовательности ID
        for table in tables:
            destination.execute(
                text(f"""
                    SELECT setval(
                        pg_get_serial_sequence(
                            'public.{table.name}', 'id'
                        ),
                        COALESCE(
                            (SELECT MAX(id) FROM public.{table.name}),
                            1
                        ),
                        EXISTS (
                            SELECT 1 FROM public.{table.name}
                        )
                    )
                """)
            )

    print("\nПеренос данных успешно завершён!")

except Exception as error:
    print("\nОшибка переноса:")
    print(error)

finally:
    local_engine.dispose()
    neon_engine.dispose()
