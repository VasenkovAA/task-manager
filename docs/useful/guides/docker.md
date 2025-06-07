### Полная инструкция: Создание базы данных PostgreSQL в Docker (для новичков)

#### 0. Предварительные шаги
**Для всех ОС:**
1. Установите Docker Desktop:
   - Windows/Mac: [Скачайте с официального сайта](https://www.docker.com/products/docker-desktop)
   - Linux (Ubuntu/Debian):
     ```bash
     sudo apt update
     sudo apt install docker.io
     sudo systemctl enable --now docker
     ```

2. Проверьте установку:
   ```bash
   docker --version
   # Должен отобразить версию Docker (например: Docker version 24.0.7)
   ```

---

#### 1. Запуск контейнера PostgreSQL
**Выполните в терминале:**
```bash
docker run \
  --name my-postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_DB=mydb \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  -d \
  postgres:16
```

**Пояснение каждого флага:**
| Флаг/Параметр               | Объяснение                                                                 |
|-----------------------------|----------------------------------------------------------------------------|
| `docker run`                | Запустить новый контейнер                                                  |
| `--name my-postgres`        | Задаем понятное имя контейнеру (можно изменить)                            |
| `-e POSTGRES_PASSWORD=...`  | **Обязательно!** Пароль для суперпользователя (минимум 8 символов)         |
| `-e POSTGRES_USER=...`      | Опционально: Имя пользователя (по умолчанию `postgres`)                    |
| `-e POSTGRES_DB=...`        | Опционально: Имя создаваемой БД (по умолчанию = имя пользователя)          |
| `-p 5432:5432`              | Проброс портов: `<хост>:<контейнер>` (доступ к БД на localhost:5432)       |
| `-v postgres-data:...`      | Сохраняет данные БД в именованном томе Docker (чтобы данные не удалились) |
| `-d`                        | Запуск в фоновом режиме (detached)                                         |
| `postgres:16`               | Образ PostgreSQL с версией 16 (можно использовать `latest`)                |

---

#### 2. Проверка работы
1. Убедитесь, что контейнер запущен:
   ```bash
   docker ps
   # Должен показать контейнер "my-postgres" со статусом "Up"
   ```

2. Просмотр логов (если нужно):
   ```bash
   docker logs my-postgres
   # Ищите строку "database system is ready to accept connections"
   ```

---

#### 3. Подключение к базе данных
**Способ 1: Через контейнер (рекомендуется для новичков)**
```bash
docker exec -it my-postgres psql -U myuser -d mydb
```
- `docker exec`: Выполнить команду внутри контейнера
- `-it`: Интерактивный режим с терминалом
- `psql`: Клиент PostgreSQL
- `-U myuser`: Имя пользователя
- `-d mydb`: Имя базы данных

**Способ 2: С вашего компьютера**
1. Установите `psql`:
   - **Windows**: [Установите PostgreSQL](https://www.postgresql.org/download/windows/)
   - **Mac**: `brew install postgresql`
   - **Linux**: `sudo apt install postgresql-client`

2. Подключитесь:
   ```bash
   psql -h localhost -p 5432 -U myuser -d mydb
   ```
   → Введите пароль `mysecretpassword`

---

#### 4. Основные команды PostgreSQL
Внутри `psql`:
```sql
-- Показать все базы данных
\l

-- Показать таблицы в текущей БД
\dt

-- Создать таблицу
CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(50));

-- Выйти из psql
\q
```

---

#### 5. Управление контейнером
| Действие                     | Команда                          |
|------------------------------|----------------------------------|
| Остановить контейнер         | `docker stop my-postgres`        |
| Запустить снова              | `docker start my-postgres`       |
| Удалить контейнер            | `docker rm my-postgres`          |
| Просмотреть тома             | `docker volume ls`               |
| Удалить том с данными        | `docker volume rm postgres-data` |

---

#### 6. Дополнительные настройки
**Добавление начальных данных:**
1. Создайте папку `init-scripts` и файл `init.sql`:
   ```sql
   CREATE TABLE employees (id SERIAL, name TEXT);
   INSERT INTO employees (name) VALUES ('Иван Петров');
   ```

2. Запустите контейнер с монтированием:
   ```bash
   docker run ... \
     -v ./init-scripts:/docker-entrypoint-initdb.d \
     postgres:16
   ```
   - Все файлы `.sql` из папки выполнятся автоматически при первом запуске

**Настройка среды:**
```bash
# Пример с дополнительными переменными
docker run ... \
  -e TZ=Europe/Moscow \
  -e POSTGRES_INITDB_ARGS="--encoding=UTF8" \
  postgres:16
```

---

#### 7. Важные нюансы для разных ОС
| ОС         | Особенности                                                                 |
|------------|-----------------------------------------------------------------------------|
| **Windows**| Используйте PowerShell вместо CMD. Для томов: путь указывать как `//c/...` |
| **Mac**    | На M1/M2 добавьте флаг `--platform linux/amd64` перед `postgres:16`        |
| **Linux**  | Может потребоваться `sudo` перед командами Docker                          |

---

#### 8. Что делать если...
- **Ошибка порта 5432**: 
  ```bash
  # Измените порт (например на 5433):
  -p 5433:5432
  ```
- **Забыли пароль**:
  ```bash
  docker exec -it my-postgres bash
  psql -U postgres
  ALTER USER myuser PASSWORD 'newpassword';
  ```
- **Нужно скопировать файл в контейнер**:
  ```bash
  docker cp myfile.sql my-postgres:/tmp/
  ```

---

#### 9. Графические инструменты (рекомендации)
1. [pgAdmin](https://www.pgadmin.org/):
   ```bash
   docker run -p 5050:80 -e PGADMIN_DEFAULT_EMAIL=admin@example.com -e PGADMIN_DEFAULT_PASSWORD=admin -d dpage/pgadmin4
   ```
2. [DBeaver](https://dbeaver.io/) - бесплатный кроссплатформенный клиент

---

**Теперь у вас есть полностью рабочая PostgreSQL в Docker!** Для проверки:
1. Подключитесь через `psql`
2. Выполните:
   ```sql
   CREATE TABLE test (id SERIAL);
   INSERT INTO test DEFAULT VALUES;
   SELECT * FROM test;
   ```
   → Должен вернуться результат `[1]`