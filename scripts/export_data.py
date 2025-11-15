import csv
import sys
from pathlib import Path
from datetime import datetime
from infrastructure.db.database import get_connection

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def export_table(table_name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # Get column names dynamically
    column_names = [desc[0] for desc in cursor.description]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"{table_name}_{timestamp}.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(column_names)
        writer.writerows(rows)

    cursor.close()
    conn.close()

    print(f"Exported {len(rows)} records from '{table_name}' to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: You must provide a table name.")
        print("Usage: python scripts/export_data.py <table_name>")
        sys.exit(1)

    table = sys.argv[1]
    export_table(table)
