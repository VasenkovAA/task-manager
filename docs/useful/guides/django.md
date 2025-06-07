### Полная инструкция по работе с Django для новичков

#### 1. Установка Django
```bash
pip install django
```
**Проверка версии:**
```bash
django-admin --version
```

---

#### 2. Создание проекта
```bash
django-admin startproject myproject
```
Структура проекта:
```
myproject/
├── manage.py         # Утилита для управления проектом
└── myproject/        # Основной пакет проекта
    ├── __init__.py
    ├── settings.py   # Настройки проекта
    ├── urls.py       # Главные URL-маршруты
    ├── asgi.py
    └── wsgi.py
```

---

#### 3. Запуск сервера разработки
```bash
python manage.py runserver
```
**Флаги:**
- `--port 8080`: Запуск на порту 8080 (по умолчанию: 8000)
- `--noreload`: Отключить авто-перезагрузку
- `--insecure`: Форсировать обслуживание статических файлов без DEBUG=True

**Пример:**
```bash
python manage.py runserver 0.0.0.0:8000  # Доступ с других устройств
```

---

#### 4. Создание приложения
```bash
python manage.py startapp myapp
```
Структура приложения:
```
myapp/
├── migrations/       # Файлы миграций БД
├── __init__.py
├── admin.py         # Регистрация моделей в админке
├── apps.py
├── models.py        # Модели данных
├── tests.py
└── views.py         # Обработчики запросов
```

**Регистрация приложения в `settings.py`:**
```python
INSTALLED_APPS = [
    ...
    'myapp',
]
```

---

#### 5. Миграции базы данных
**a. Создание миграций:**
```bash
python manage.py makemigrations
```
**Флаги:**
- `--dry-run`: Показать план без создания файлов
- `--name my_migration`: Имя миграции
- `myapp`: Создать миграции только для конкретного приложения

**b. Применение миграций:**
```bash
python manage.py migrate
```
**Флаги:**
- `--fake`: Отметить миграцию как применённую без выполнения SQL
- `myapp 0001`: Применить конкретную миграцию

---

#### 6. Административная панель
**a. Создание суперпользователя:**
```bash
python manage.py createsuperuser
```
**b. Регистрация модели в `admin.py`:**
```python
from .models import MyModel

admin.site.register(MyModel)
```

---

#### 7. Работа с моделями (models.py)
**Пример модели:**
```python
from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=50)
    published_date = models.DateField(auto_now_add=True)
```

**Команды для работы с БД:**
- `python manage.py dbshell`: Открыть консоль СУБД
- `python manage.py inspectdb`: Генерировать модели по существующей БД

---

#### 8. Оболочка Django (Shell)
```bash
python manage.py shell
```
**С флагом:**
- `--command='import django; print(django.__version__)'`: Выполнить команду и выйти

**Пример работы:**
```python
from myapp.models import Book
Book.objects.create(title="Django for Beginners", author="William S. Vincent")
Book.objects.all().count()
```

---

#### 9. Статические файлы
**a. Добавить в `settings.py`:**
```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]  # Для разработки
STATIC_ROOT = BASE_DIR / "staticfiles"    # Для продакшена
```

**b. Сборка статики:**
```bash
python manage.py collectstatic
```
**Флаги:**
- `--noinput`: Без подтверждения
- `--clear`: Очистить перед сборкой

---

#### 10. Тестирование
```bash
python manage.py test
```
**Флаги:**
- `myapp.tests.TestClass`: Запустить конкретный тест
- `--keepdb`: Сохранить тестовую БД
- `--parallel`: Параллельное выполнение тестов

**Пример теста:**
```python
# tests.py
from django.test import TestCase
from .models import Book

class BookTestCase(TestCase):
    def test_book_creation(self):
        Book.objects.create(title="Test Book")
        self.assertEqual(Book.objects.count(), 1)
```

---

#### 11. Управление приложениями
**a. Список установленных команд:**
```bash
python manage.py help
```

**b. Проверка настроек:**
```bash
python manage.py check
```
**Флаги:**
- `--deploy`: Проверка настроек для продакшена
- `--fail-level WARNING`: Уровень критичности ошибок

---

#### 12. Другие полезные команды
**a. Очистка сессий:**
```bash
python manage.py clearsessions
```

**b. Сброс паролей:**
```bash
python manage.py changepassword <username>
```

**c. Экспорт данных:**
```bash
python manage.py dumpdata myapp.Book --format=json > books.json
```

**d. Импорт данных:**
```bash
python manage.py loaddata books.json
```

---

### Основные файлы проекта:
1. **settings.py**
   - `DEBUG`: Режим отладки (False в продакшене!)
   - `ALLOWED_HOSTS`: Доверенные домены (['*'] для разработки)
   - `DATABASES`: Настройки БД (по умолчанию SQLite)
   - `LANGUAGE_CODE`: Язык ('ru-RU' для русского)

2. **urls.py**
   ```python
   from django.urls import path
   from . import views
   
   urlpatterns = [
       path('books/', views.book_list, name='book-list'),
   ]
   ```

3. **views.py**
   ```python
   from django.http import HttpResponse
   
   def book_list(request):
       return HttpResponse("Список книг")
   ```

---

### Советы для новичков:
1. **Виртуальное окружение:** Всегда используйте `venv` или `virtualenv`
2. **Git:** Игнорируйте файлы в `.gitignore`:
   ```
   __pycache__/
   *.sqlite3
   .env
   staticfiles/
   ```
3. **Переменные окружения:** Храните секреты (SECRET_KEY) в `.env` (используйте библиотеку `python-dotenv`)
4. **Структура проекта:**
   ```
   myproject/
   ├── apps/          # Ваши приложения
   ├── static/        # Локальные статические файлы
   ├── templates/     # Глобальные шаблоны
   └── myproject/     # Настройки проекта
   ```

Для углубленного изучения:
- Официальная документация: https://docs.djangoproject.com/
- Django REST Framework: для создания API
- Django Channels: для WebSockets
- Django Debug Toolbar: для отладки