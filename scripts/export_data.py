import csv
from pathlib import Path
from datetime import datetime
from infrastructure.db.database import get_connection

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def export_repositories():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT repo_id, full_name, stars, last_crawled FROM repositories")
    rows = cursor.fetchall()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"repositories_{timestamp}.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["repo_id", "full_name", "stars", "last_crawled"])
        # Write rows
        writer.writerows(rows)

    cursor.close()
    conn.close()
    print(f"Exported {len(rows)} repositories to {output_file}")


if __name__ == "__main__":
    export_repositories()