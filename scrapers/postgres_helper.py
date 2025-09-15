# postgres_helper.py
import psycopg2

DB_CONFIG = {
    'host': '178.79.182.27',
    'user': 'briqpay',
    'password': 'briqpay111',
    'dbname': 'briqpay'
}

def insert_to_postgres(data_dict):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        columns = data_dict.keys()
        values = [data_dict[col] for col in columns]

        sql = f"""
            INSERT INTO stg_price_77diamonds_scrape ({', '.join(columns)})
            VALUES ({', '.join(['%s'] * len(columns))})
        """

        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Inserted into PostgreSQL")

    except Exception as e:
        print(f"❌ PostgreSQL insert failed: {e}")
