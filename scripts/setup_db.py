from pathlib import Path
from src.app.config import settings
import psycopg2

def setup():
    sql_file = Path(__file__).parent.parent / 'infrastructure' / 'db' / 'migrations.sql'

    with open(sql_file, "r") as f:
        migration_sql = f.read()

    conn = psycopg2.connect(settings.DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute(migration_sql)

    conn.commit()
    cursor.close()
    conn.close()

    print("Database setup completed using migrations.sql")


if __name__ == "__main__":
    setup()
