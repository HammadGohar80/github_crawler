import psycopg2
from psycopg2.extras import RealDictCursor
from src.app.config import settings

def get_connection():
    return psycopg2.connect(settings.POSTGRES_URL, cursor_factory=RealDictCursor)
