import psycopg2
from psycopg2 import OperationalError, DatabaseError

pg_conn = None
pg_cursor = None

try:
    pg_conn = psycopg2.connect(
        host="178.79.182.27",
        database="briqpay",
        user="briqpay",
        password="briqpay111"
    )
    pg_conn.autocommit = True
    pg_cursor = pg_conn.cursor()
    print("PostgreSQL connection established successfully.")

except OperationalError as e:
    print(f"OperationalError: Could not connect to PostgreSQL - {e}")
except DatabaseError as e:
    print(f"DatabaseError: Database operation failed - {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

def close_connection():
    """Safely closes the cursor and connection."""
    try:
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()
        print("PostgreSQL connection closed.")
    except Exception as e:
        print(f"Error closing PostgreSQL connection: {e}")


# pg_conn = psycopg2.connect(
#     host="178.79.182.27",
#     database="briqpay",
#     user="briqpay",
#     password="briqpay111"
# )
# pg_conn.autocommit = True
# pg_cursor = pg_conn.cursor()

