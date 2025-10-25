<h1 align="center">🪙 Kibiki Web</h1>

<p align="center">
  <b>Многофункциональный веб-магазин с внутренней валютой на Flask + PostgreSQL</b><br>
  Управление пользователями, балансами, товарами и историей покупок
</p>

<p align="center">
  <a href="https://github.com/KrutoiXatcker/kibiki_web/stargazers">
    <img src="https://img.shields.io/github/stars/KrutoiXatcker/kibiki_web?color=yellow&style=flat-square" alt="Stars">
  </a>
  <a href="https://github.com/KrutoiXatcker/kibiki_web/issues">
    <img src="https://img.shields.io/github/issues/KrutoiXatcker/kibiki_web?color=orange&style=flat-square" alt="Issues">
  </a>
  <a href="https://github.com/KrutoiXatcker/kibiki_web/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/KrutoiXatcker/kibiki_web?style=flat-square" alt="License">
  </a>
</p>

---

## 🚀 О проекте

**Kibiki Web** — это веб-платформа, написанная на **Flask (Python)**, с базой данных **PostgreSQL**, предназначенная для управления пользователями и внутренней валютой — *кибиками*.  
Приложение включает в себя личный кабинет, магазин товаров, систему покупок и панель администратора.

---

## ✨ Основные возможности

### 👤 Пользователь
- 🔐 Авторизация / выход из системы  
- 💰 Просмотр баланса  
- 🛍 Покупка товаров в магазине  
- 🧾 Просмотр своей истории покупок  

### 🛠 Администратор
- 👥 Управление пользователями (создание, удаление, редактирование)  
- 💵 Настройка балансов кибиков  
- 🧰 Добавление / редактирование товаров  
- 📊 Просмотр всех покупок  

---

## 📁 Структура проекта

```
kibiki_web/
├── app.py                 # Основное приложение Flask
├── db_init.py             # Инициализация базы данных
├── templates/             # HTML-шаблоны (Jinja2)
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── products.html
│   ├── purchases.html
│   ├── admin.html
│   ├── admin_products.html
│   └── admin_purchases.html
├── static/
│   ├── style.css
│   └── ...
└── README.md
```

---

## ⚙️ Установка и запуск

### 1️⃣ Клонирование репозитория

```bash
git clone https://github.com/KrutoiXatcker/kibiki_web.git
cd kibiki_web
```

---

### 2️⃣ Создание виртуального окружения и установка зависимостей

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install flask psycopg2-binary werkzeug
```

---

### 3️⃣ Настройка PostgreSQL

Создай базу и пользователя:

```sql
CREATE DATABASE test2_utf8 ENCODING 'UTF8';
CREATE USER jems WITH PASSWORD '1111';
GRANT ALL PRIVILEGES ON DATABASE test2_utf8 TO jems;
```

---

### 4️⃣ Инициализация таблиц

```bash
python db_init.py
```

Таблицы:
- `users`
- `products`
- `purchases`

---

### 5️⃣ Запуск сервера

```bash
python app.py
```

Открой в браузере:  
👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧩 Структура базы данных

### Таблица `users`
| Поле | Тип | Описание |
|------|------|----------|
| id | SERIAL | ID |
| username | VARCHAR(50) | Логин |
| password_hash | TEXT | Хэш пароля |
| fullname | VARCHAR(100) | Полное имя |
| kibiki | INTEGER | Баланс кибиков |
| is_admin | BOOLEAN | Флаг администратора |

### Таблица `products`
| Поле | Тип | Описание |
|------|------|----------|
| id | SERIAL | ID товара |
| name | VARCHAR(100) | Название |
| description | TEXT | Описание |
| price | INTEGER | Стоимость |
| image | TEXT | URL изображения |

### Таблица `purchases`
| Поле | Тип | Описание |
|------|------|----------|
| id | SERIAL | ID покупки |
| username | VARCHAR(50) | Покупатель |
| product_id | INTEGER | ID товара |
| price_at_purchase | INTEGER | Цена |
| created_at | TIMESTAMP | Дата покупки |

---

## 🧭 Основные маршруты

| URL | Метод | Доступ | Описание |
|-----|--------|--------|----------|
| `/login` | GET/POST | Все | Вход в систему |
| `/logout` | GET | Авториз. | Выход |
| `/dashboard` | GET | Пользователь | Личный кабинет |
| `/products` | GET | Пользователь | Каталог |
| `/buy/<id>` | POST | Пользователь | Покупка товара |
| `/purchases` | GET | Пользователь | История своих покупок |
| `/admin` | GET | Админ | Панель пользователей |
| `/admin/products` | GET | Админ | Управление товарами |
| `/admin/purchases` | GET | Админ | История всех покупок |

---

## 💾 Добавление администратора вручную

Если у тебя нет админа — создай его вручную:

```sql
INSERT INTO users (username, password_hash, fullname, kibiki, is_admin)
VALUES ('admin', crypt('password', gen_salt('bf')), 'Главный админ', 0, TRUE);
```

---

## 🎨 Интерфейс

🖼 Интерфейс построен на чистом HTML + CSS (через Jinja2):
- карточки товаров,  
- мягкие кнопки,  
- таблицы в админке,  
- единый стиль оформления.

---

## 🔒 Безопасность

- Пароли хэшируются с помощью `werkzeug.security`
- SQL-запросы безопасны (`%s` плейсхолдеры)
- Сессии Flask защищены `secret_key`
- Ограничения доступа по ролям

---

## 🧠 Как всё работает

1. Пользователь авторизуется — Flask создаёт сессию  
2. При покупке проверяется баланс  
3. Если хватает кибиков — происходит списание и запись в `purchases`  
4. Пользователь видит историю в `/purchases`  
5. Админ видит всё в `/admin/purchases`

---

## 📊 Будущие улучшения

- [X] Редактирование товаров  
- [ ] Поиск и фильтры  
- [ ] REST API (JSON)  
- [ ] Telegram-уведомления  
- [ ] Графики продаж  

---

## 🧾 Лицензия

Этот проект распространяется по лицензии **MIT**.  
Свободно для личного и коммерческого использования.

---

## 👨‍💻 Автор

**Valdemar / KrutoiXatcker**  
📦 Репозиторий: [github.com/KrutoiXatcker/kibiki_web](https://github.com/KrutoiXatcker/kibiki_web)

---

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-Flask-blue?style=for-the-badge&logo=flask">
  <img src="https://img.shields.io/badge/Database-PostgreSQL-blue?style=for-the-badge&logo=postgresql">
  <img src="https://img.shields.io/badge/Language-Python%203.11-yellow?style=for-the-badge&logo=python">
</p>
