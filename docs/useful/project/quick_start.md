### Запуск task_planner

---

### **1. Без Docker (локальная среда)**

#### Шаги:

**1.1. Настройка виртуального окружения**

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows
```

**1.2. Установка зависимостей**  
Установите зависимости:

```bash
pip install -r requirements.txt
```

**1.3. Создание `.env` файла**  

В корне django проекта (рядом с `manage.py`):
```env
SECRET_KEY=ваш_секретный_ключ
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=mydb
DB_USER=myuser
DB_PASSWORD=mypassword
DB_HOST=localhost
DB_PORT=5432
```


**1.4.1. Запуск PostgreSQL локально**

- Установите PostgreSQL: https://www.postgresql.org/download/
- Создайте БД и пользователя:
  ```sql
  CREATE DATABASE mydb;
  CREATE USER myuser WITH PASSWORD 'mypassword';
  GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
  ```
  Либо через GUI.

**1.4.2. Запуск PostgreSQL в docker образе**

**Запуск контейнера PostgreSQL**  

```bash
docker run --name my-postgres \
  -e POSTGRES_DB=mydb \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -p 5432:5432 \
  -d postgres:13
```  

- `--name` — имя контейнера.  
- `-e` — переменные окружения (логин, пароль, имя БД).  
- `-p` — проброс порта (`локальный:контейнерный`).  
- `-d` — запуск в фоне.  


**Проверка работы**  
- Подключитесь к БД из терминала:  
  ```bash
  docker exec -it my-postgres psql -U myuser -d mydb
  ```  
- Django сможет работать с БД, как если бы PostgreSQL был установлен локально.  

**Остановка и удаление**  
```bash
docker stop my-postgres
docker rm my-postgres
```  


**1.6. Применение миграций и запуск сервера**

```bash
python manage.py migrate
python manage.py runserver
```

Приложение доступно на http://localhost:8000.
**ПОРТ МОЖЕТ ПОМЕНЯТЬСЯ**, актуальный порт написан в консолит после запуска.

---
