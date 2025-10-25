import psycopg2
import os

def init_db():
    DB_HOST = "127.0.0.1"
    DB_NAME = "test2_utf8"
    DB_USER = "jems"
    DB_PASSWORD = "1111"

    print("DEBUG HOST:", repr(DB_HOST))
    print("DEBUG NAME:", repr(DB_NAME))
    print("DEBUG USER:", repr(DB_USER))
    print("DEBUG PASS:", repr(DB_PASSWORD))

    print("\nENV CHECK >>>")
    for key in ["PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE", "DATABASE_URL", "PGCLIENTENCODING"]:
        print(key, "=>", repr(os.getenv(key)))

    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username VARCHAR(50) PRIMARY KEY,
        password_hash TEXT NOT NULL,
        fullname VARCHAR(100),
        kibiki INTEGER DEFAULT 0,
        is_admin BOOLEAN DEFAULT FALSE
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price INTEGER NOT NULL CHECK (price >= 0),
        image TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        product_id INTEGER NOT NULL,
        price_at_purchase INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """)

    cur.execute("SELECT COUNT(*) FROM products;")
    count = cur.fetchone()[0]

    if count == 0:
        print("Заполняю магазин стартовыми товарами...")
        cur.execute("""
                INSERT INTO products (name, description, price, image)
                VALUES
                ('Редкий котёнок', 'Милый котёнок, который будет следовать за тобой в реальности... или нет.', 150, '/static/images/cat.jpg'),
                ('КриптоАкселератор', 'Ускоряет твою жизнь в 2 раза (по словам производителя).', 500, '/static/images/crypto.jpg'),
                ('Легендарная монета', 'Историческая реликвия, найденная в подвале у бабушки.', 1000, '/static/images/coin.jpg'),
                ('Премиум стикерпак', '100 уникальных стикеров для WhatsApp.', 300, '/static/images/stickers.jpg')
            """)
    conn.commit()
    cur.close()
    conn.close()
    print("TABLE CHECK DONE")

if __name__ == "__main__":
    init_db()
