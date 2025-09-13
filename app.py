import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Подключение к БД
def get_db_connection():
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="test2",
        user="jems",
        password="1111"
    )
    return conn

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

@app.route('/products')
def products():
    if 'username' not in session:
        return redirect(url_for('login'))

    products_list = [
        {"id": 1, "name": "Редкий котёнок", "price": 150, "image": "/static/images/cat.jpg", "description": "Милый котёнок, который будет следовать за тобой в реальности... или нет."},
        {"id": 2, "name": "КриптоАкселератор", "price": 500, "image": "/static/images/crypto.jpg", "description": "Ускоряет твою жизнь в 2 раза (по словам производителя)."},
        {"id": 3, "name": "Легендарная монета", "price": 1000, "image": "/static/images/coin.jpg", "description": "Историческая реликвия, найденная в подвале у бабушки."},
        {"id": 4, "name": "Премиум стикерпак", "price": 300, "image": "/static/images/stickers.jpg", "description": "100 уникальных стикеров для WhatsApp."}
    ]

    return render_template('products.html', products=products_list, kibiki=session['kibiki'])

@app.route('/buy/<int:product_id>', methods=['POST'])
def buy_product(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    products_prices = {
        1: 150,
        2: 500,
        3: 1000,
        4: 300
    }

    price = products_prices.get(product_id)
    if not price:
        flash("Товар не найден.", "danger")
        return redirect(url_for('products'))

    if session['kibiki'] < price:
        flash("Недостаточно кибиков!", "warning")
        return redirect(url_for('products'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET kibiki = kibiki - %s WHERE username = %s", (price, session['username']))
    conn.commit()
    cur.close()
    conn.close()

    session['kibiki'] -= price
    flash(f"Покупка успешна! Ты потратил {price} кибиков.", "success")
    return redirect(url_for('products'))

# === АДМИН-ПАНЕЛЬ ===

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

# Функции управления кибиками (остаются без изменений)

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

if __name__ == '__main__':
    app.run(debug=True)
