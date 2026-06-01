# 💰 ExpensesManager

A personal finance tracking web application built with Django. Track your income and expenses, manage your budget, and get a clear picture of your financial activity.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + Django |
| Templating | Jinja2 |
| Database | PostgreSQL 15 |
| Cache / Sessions | Redis 7 |
| Containerization | Docker + Docker Compose |

---

## ✨ Features

- 📥 Track **income** and 📤 **expenses**
- 🗂 Categorize financial operations
- ✏️ Create, edit, and delete transactions
- 👤 User profile management
- 📊 Overview dashboard of financial activity
- 🔐 User authentication

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/expenses-manager.git
cd expenses-manager
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
SECRET_KEY=your-secret-key-here
DB_NAME=expenses
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6380
```

### 3. Build and start containers

```bash
docker-compose up --build
```

### 4. Run database migrations

```bash
docker exec -it django_web python manage.py migrate
```

### 5. Create a superuser (admin account)

```bash
docker exec -it django_web python manage.py createsuperuser
```

### 6. Open in browser

```
http://localhost:8002
```

Admin panel:
```
http://localhost:8002/admin
```

---

## 🐳 Docker Services

| Service | Container | Port |
|---|---|---|
| Django App | `django_web` | `8002` |
| PostgreSQL | `postgres_db` | `5434` |
| Redis | `redis_server` | `6380` |

---

## 🔧 Useful Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (wipes DB)
docker-compose down -v

# View logs
docker-compose logs -f

# Django shell
docker exec -it django_web python manage.py shell

# Run migrations
docker exec -it django_web python manage.py migrate

# Collect static files
docker exec -it django_web python manage.py collectstatic
```

---

## 🌍 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | — |
| `DB_NAME` | PostgreSQL database name | `expenses` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_HOST` | DB host (Docker service name) | `db` |
| `DB_PORT` | DB port (internal) | `5432` |
| `REDIS_HOST` | Redis host (Docker service name) | `redis` |
| `REDIS_PORT` | Redis port | `6380` |

> ⚠️ **Never commit your `.env` file.** It contains sensitive credentials.
