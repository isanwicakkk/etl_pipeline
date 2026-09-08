from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


DB_USER = "myuser"
DB_PASSWORD = "password123"
DB_HOST = "127.0.0.1"
DB_PORT = 5433
DB_NAME = "mydb"


url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)


engine = create_engine(url)


try:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT current_user, current_database();")
        )

        print("BERHASIL TERHUBUNG!")
        print(result.fetchone())

except Exception as e:
    print("GAGAL TERHUBUNG!")
    print(e)