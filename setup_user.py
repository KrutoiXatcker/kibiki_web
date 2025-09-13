import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash

def create_admin_user():
    try:
        # Подключение к существующей базе данных
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="test2",
            user="jems",
            password="1111"
        )
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Проверим структуру таблицы и добавим поле fullname если нужно
        try:
            cur.execute("SELECT fullname FROM users LIMIT 1")
        except psycopg2.errors.UndefinedColumn:
            print("Добавляем поле fullname в таблицу users...")
            cur.execute("ALTER TABLE users ADD COLUMN fullname VARCHAR(100)")
            conn.commit()
            print("Поле fullname добавлено!")
        
        # Создание администратора
        username = "admin"
        password = "admin123"
        fullname = "Администратор Системы"
        kibiki = 1000
        is_admin = True
        
        password_hash = generate_password_hash(password)
        
        try:
            cur.execute("""
                INSERT INTO users (username, password_hash, fullname, kibiki, is_admin) 
                VALUES (%s, %s, %s, %s, %s)
            """, (username, password_hash, fullname, kibiki, is_admin))
            conn.commit()
            print(f"Администратор '{username}' успешно создан!")
            print(f"Логин: {username}")
            print(f"Пароль: {password}")
            print(f"ФИО: {fullname}")
            print(f"Кибики: {kibiki}")
            
        except psycopg2.IntegrityError:
            conn.rollback()
            print(f"Пользователь '{username}' уже существует!")
            
            # Попробуем обновить существующего пользователя до админа
            cur.execute("""
                UPDATE users 
                SET password_hash = %s, fullname = %s, is_admin = %s, kibiki = %s 
                WHERE username = %s
            """, (password_hash, fullname, is_admin, kibiki, username))
            conn.commit()
            print(f"Пользователь '{username}' обновлен до администратора!")
            print(f"Новый пароль: {password}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Убедитесь, что база данных test2 существует и доступна")
    
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def list_users():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="test2",
            user="jems",
            password="1111"
        )
        cur = conn.cursor(cursor_factory=DictCursor)
        
        cur.execute("SELECT username, fullname, kibiki, is_admin FROM users ORDER BY username")
        users = cur.fetchall()
        
        print("\nСписок пользователей:")
        print("-" * 60)
        for user in users:
            admin_status = "АДМИН" if user['is_admin'] else "ПОЛЬЗ"
            fullname = user['fullname'] if user['fullname'] else "Не указано"
            print(f"{user['username']:15} | {fullname:20} | {user['kibiki']:6} | {admin_status}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при получении списка пользователей: {e}")

if __name__ == "__main__":
    print("Создание/обновление администратора...")
    create_admin_user()
    print("\n" + "="*50)
    list_users()
