from database import get_connection

class RepositoryRepository:

    def upsert_repo(self, repo_id: int, full_name: str, stars: int):
        conn = get_connection()
        cur = conn.cursor()

        query = """
        INSERT INTO repositories (repo_id, full_name, stars)
        VALUES (%s, %s, %s)
        ON CONFLICT (repo_id)
        DO UPDATE SET stars = EXCLUDED.stars, last_crawled = NOW()
        """
        cur.execute(query, (repo_id, full_name, stars))
        conn.commit()
        conn.close()

    def insert_history(self, repo_id: int, stars: int):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO stars_history (repo_id, stars) VALUES (%s, %s)",
            (repo_id, stars),
        )

        conn.commit()
        conn.close()
