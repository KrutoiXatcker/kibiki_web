import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
from werkzeug.utils import secure_filename
from psycopg2.extras import DictCursor
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # лимит 5 МБ, можно менять
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Подключение к БД
def allowed_file(filename: str) -> bool:
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    )

def get_db_connection():
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="test2_utf8",
        user="jems",
        password="1111"
    )
    return conn


# ================== АВТОРИЗАЦИЯ ==================

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/x-icon'
    )

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            session['fullname'] = user['fullname']
            session['is_admin'] = user['is_admin']
            session['kibiki'] = user['kibiki']
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))


# ================== КАБИНЕТ ПОЛЬЗОВАТЕЛЯ ==================

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT kibiki, fullname FROM users WHERE username = %s", (session['username'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    session['kibiki'] = user['kibiki']
    session['fullname'] = user['fullname']

    return render_template('dashboard.html', kibiki=session['kibiki'], fullname=session['fullname'])


# ================== АДМИН: УПРАВЛЕНИЕ ТОВАРАМИ ==================

@app.route('/admin/products')
def admin_products():
    if 'username' not in session or not session.get('is_admin'):
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT id, name, description, price, image FROM products ORDER BY id;")
    products_list = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin_products.html', products=products_list)


@app.route('/admin/products/create', methods=['POST'])
def admin_create_product():
    if 'username' not in session or not session.get('is_admin'):
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('login'))

    name = request.form['name']
    description = request.form.get('description', '')
    price = int(request.form['price'])

    # обработка файла
    image_path = request.form.get('image', '').strip()  # резерв, если ввели URL вручную
    file = request.files.get('image_file')

    if file and file.filename != '':
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, filename)
            file.save(save_path)

            # путь, который будет храниться в БД и использоваться в <img src=...>
            image_path = f"/static/uploads/{filename}"
        else:
            flash("Неверный формат изображения. Разрешено: png, jpg, jpeg, gif, webp", "danger")
            return redirect(url_for('admin_products'))

    if not name or price < 0:
        flash("Неверные данные товара.", "danger")
        return redirect(url_for('admin_products'))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO products (name, description, price, image) VALUES (%s, %s, %s, %s)",
            (name, description, price, image_path)
        )
        conn.commit()
        flash("Товар добавлен!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка при добавлении товара: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin_products'))


@app.route('/admin/products/edit/<int:product_id>', methods=['POST'])
def admin_edit_product(product_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('login'))

    name = request.form['name']
    description = request.form.get('description', '')
    price = int(request.form['price'])

    # старое значение пути к картинке
    current_image = request.form.get('current_image', '').strip()

    # может прийти либо новый URL, либо загруженный файл
    new_image_url = request.form.get('image', '').strip()
    file = request.files.get('image_file')

    final_image_path = current_image  # по умолчанию не меняем

    # приоритет: если загрузили новый файл — используем его
    if file and file.filename != '':
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, filename)
            file.save(save_path)
            final_image_path = f"/static/uploads/{filename}"
        else:
            flash("Неверный формат изображения. Разрешено: png, jpg, jpeg, gif, webp", "danger")
            return redirect(url_for('admin_products'))
    # если файла нет, но админ вписал новый URL руками — берём его
    elif new_image_url:
        final_image_path = new_image_url

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE products
            SET name = %s, description = %s, price = %s, image = %s
            WHERE id = %s
        """, (name, description, price, final_image_path, product_id))
        conn.commit()
        flash("Товар обновлён!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка при обновлении товара: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin_products'))


@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        flash("Товар удалён.", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка при удалении товара: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin_products'))


# ================== МАГАЗИН (ОБЩЕДОСТУПНЫЕ ТОВАРЫ) ==================

@app.route('/products')
def products():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT id, name, description, price, image FROM products ORDER BY id;")
    products_list = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        'products.html',
        products=products_list,
        kibiki=session['kibiki']
    )


# ================== ИСТОРИЯ ПОКУПОК ПОЛЬЗОВАТЕЛЯ ==================

@app.route('/purchases')
def my_purchases():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("""
        SELECT p.id,
               pr.name AS product_name,
               pr.image,
               p.price_at_purchase,
               p.created_at
        FROM purchases p
        JOIN products pr ON pr.id = p.product_id
        WHERE p.username = %s
        ORDER BY p.created_at DESC;
    """, (username,))
    purchases_list = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        'purchases.html',
        purchases=purchases_list,
        kibiki=session.get('kibiki', 0),
        fullname=session.get('fullname', username)
    )


# ================== ИСТОРИЯ ПОКУПОК ДЛЯ АДМИНА ==================

@app.route('/admin/purchases')
def admin_purchases():
    if 'username' not in session or not session.get('is_admin'):
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("""
        SELECT p.id,
               p.username,
               pr.name AS product_name,
               p.price_at_purchase,
               p.created_at
        FROM purchases p
        JOIN products pr ON pr.id = p.product_id
        ORDER BY p.created_at DESC;
    """)
    purchases_all = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        'admin_purchases.html',
        purchases=purchases_all
    )


# ================== ПОКУПКА ТОВАРА ==================

@app.route('/buy/<int:product_id>', methods=['GET', 'POST'])
def buy_product(product_id):
    from flask import request

    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)

    try:
        # 1. достаём товар
        cur.execute(
            "SELECT id, name, price FROM products WHERE id = %s",
            (product_id,)
        )
        product = cur.fetchone()
        if not product:
            flash("Товар не найден.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for('products'))

        price = product['price']

        # 2. читаем баланс пользователя с блокировкой
        cur.execute(
            "SELECT kibiki FROM users WHERE username = %s FOR UPDATE",
            (username,)
        )
        user_row = cur.fetchone()
        if not user_row:
            flash("Пользователь не найден.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for('products'))

        current_kibiki = user_row['kibiki']

        if current_kibiki < price:
            flash("Недостаточно кибиков!", "warning")
            cur.close()
            conn.close()
            return redirect(url_for('products'))

        # 3. списываем кибики
        new_balance = current_kibiki - price
        cur.execute(
            "UPDATE users SET kibiki = %s WHERE username = %s",
            (new_balance, username)
        )

        # 4. пишем историю в purchases
        cur.execute(
            """
            INSERT INTO purchases (username, product_id, price_at_purchase)
            VALUES (%s, %s, %s)
            """,
            (username, product['id'], price)
        )

        conn.commit()

        # 5. обновляем сессию
        session['kibiki'] = new_balance

        flash(f"Покупка успешна! Ты купил: {product['name']} за {price} кибиков.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Ошибка при покупке: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('products'))


# ================== АДМИН-ПАНЕЛЬ (ПОЛЬЗОВАТЕЛИ) ==================

@app.route('/admin')
def admin():
    if 'username' not in session or not session.get('is_admin'):
        flash("Доступ запрещён.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT username, fullname, kibiki, is_admin FROM users ORDER BY username")
    users = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin.html', users=users)

@app.route('/admin/create', methods=['POST'])
def create_user():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    username = request.form['username']
    password = request.form['password']
    fullname = request.form.get('fullname', '')
    kibiki = int(request.form.get('kibiki', 0))
    is_admin = bool(request.form.get('is_admin'))

    if not username or not password:
        flash("Имя пользователя и пароль обязательны!", "danger")
        return redirect(url_for('admin'))

    hash_pw = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, fullname, kibiki, is_admin) VALUES (%s, %s, %s, %s, %s)",
            (username, hash_pw, fullname, kibiki, is_admin)
        )
        conn.commit()
        flash(f"Пользователь {username} создан!", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash("Пользователь с таким именем уже существует!", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin'))

@app.route('/admin/delete/<username>')
def delete_user(username):
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    cur.close()
    conn.close()

    flash(f"Пользователь {username} удалён.", "info")
    return redirect(url_for('admin'))

@app.route('/admin/edit_fullname', methods=['POST'])
def edit_fullname():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    username = request.form['username']
    fullname = request.form['fullname']

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET fullname = %s WHERE username = %s",
            (fullname, username)
        )
        conn.commit()
        flash(f"ФИО пользователя {username} обновлено!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка при обновлении ФИО: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin'))

@app.route('/admin/add_kibiki', methods=['POST'])
def add_kibiki():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    username = request.form['username']
    amount = int(request.form['amount'])

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET kibiki = kibiki + %s WHERE username = %s",
            (amount, username)
        )
        conn.commit()
        flash(f"Добавлено {amount} кибиков пользователю {username}!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка при добавлении кибиков: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin'))

@app.route('/admin/remove_kibiki', methods=['POST'])
def remove_kibiki():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    username = request.form['username']
    amount = int(request.form['amount'])

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT kibiki FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user and user[0] >= amount:
            cur.execute(
                "UPDATE users SET kibiki = kibiki - %s WHERE username = %s",
                (amount, username)
            )
            conn.commit()
            flash(f"Удалено {amount} кибиков у пользователя {username}!", "success")
        else:
            flash(f"Недостаточно кибиков у пользователя {username}!", "warning")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка при удалении кибиков: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin'))

@app.route('/admin/set_kibiki', methods=['POST'])
def set_kibiki():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    username = request.form['username']
    amount = int(request.form['amount'])

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET kibiki = %s WHERE username = %s",
            (amount, username)
        )
        conn.commit()
        flash(f"Установлено {amount} кибиков для пользователя {username}!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка при установке кибиков: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin'))


# ================== RUN ==================

if __name__ == '__main__':
    app.run(debug=True)
