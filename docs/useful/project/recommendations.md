
### 1. GIT.

Система контроля версия, все команды, которые в будете видеть в руководстве рассчитаны под нее.

[GIT](https://git-scm.com/).

В связи с тем что репозиторий приватный вам будет необходимо авторизоваться. Это можно сделать несколькими путями. Наиболее рекомендованный способ - `ssh`.

### 2. Python.

Python непосредственно язык разработки. Мы используем не ниже Python 3.11.

[Python](https://www.python.org/downloads/release/python-3110/)

Для сборки проекта он обязателен.

Установка Python 3.12
#### Windows:
1. Скачайте установщик Python 3.12 с официального сайта Python.
2. Установите Python, обязательно отметив галочку "Add Python to PATH".
3. Проверьте установку, запустив команду в терминале:
```
python --version
```
#### macOS/Linux:
1. Убедитесь, что у вас установлен менеджер пакетов ( brew на macOS, apt или
yum на Linux).
2. Установите Python:
macOS:
```bash
install python@3.12
```
Ubuntu/Debian:
```bash
sudo apt update && sudo apt install python3.12
```
Fedora:
```bash
sudo dnf install python3.12
```
3. Проверьте установку:
```
python3 --version
```
Примечание: Python 3.12 уже включает модули venv и pip , поэтому их дополнительно
устанавливать не нужно.

### 3. PostgreSQL.

PostgreSQL мы используем в качестве основной базы данных, под которую все было написано. Использование других баз не гарантирует стабильности работы.

[PostgreSQL](https://www.postgresql.org/)

Для сборки проекта он не обязателен, если вы подключаетесь к удаленной базе, но для разработки он очень полезен. Без него вы не сможете работать локально.

### 4. Docker.

Docker мы используем для создания контейнеров. Это позволяет нам создавать отдельные контейнеры с базами данных для локального тестирования в приближенных к реальности условиях.

[Docker](https://www.docker.com/)

Для сборки проекта он не обязателен, если вы подключаетесь к удаленной базе, но для разработки он очень полезен. Без него вы не сможете работать локально.

### 5. Docker Compose.

Docker Compose мы используем для управления контейнерами. Это позволяет нам создавать сразу группу контейнеров и корректно их связать.

[Docker Compose](https://docs.docker.com/compose/)

Для сборки проекта он не обязателен, если вы подключаетесь к удаленной базе, но для разработки он очень полезен. Без него вы не сможете работать локально.

### 6. PGAdmin4 или DBeaver для управления базами данных.

Для управления базами данных мы используем PGAdmin4 или DBeaver. Это позволяет нам корректно отлаживаться и легко находить ошибки.

Для сборки проекта он не обязателен, если вы подключаетесь к удаленной базе, но для разработки он очень полезен. Без него вы не сможете работать локально. Для backend разработчиков необходим.

---

### 1. Среды разработки.

Для работы с проектом рекомендуем использовать:

1.1. [VS Code](https://code.visualstudio.com/).

1.2. [PyCharm](https://www.jetbrains.com/pycharm/).

### 2. Ruff.

Установите плагин `ruff` для своего ide, это сильно облегчит нахождение ошибок форматирования и часть ошибок он сам может поправить.

VS code - [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

PyCharm - [Ruff](https://plugins.jetbrains.com/plugin/20574-ruff).

### 3. Venv.

Для работы с проектом рекомендуем создать виртуальную среду python. Создать ее можно так:

```bash
python -m venv venv
```

Активируйте виртуальное окружение:
Windows:
```bash
.\venv\Scripts\activate
```
macOS/Linux:
```bash
source venv/bin/activate
```
3. Убедитесь, что виртуальное окружение активно (должно быть указание (venv) в
начале строки терминала).


После этого уже ставить сюда все библиотеки.


### 4. Разработка.

Советуем разрабатываться без контейнера и запускать проект командой:

```bash
python3 manage.py runserver
```

При изменении функционального кода перезапуск сервера происходит автоматически(при сохранении изменений).

При разработке в контейнере не всегда изменения собирается автоматически.

**Перед созданием коммита рекомендуем проверить собирается ли проект в контейнере**

Для просмотра базы рекомендуем использовать [PGAdmin4](https://www.pgadmin.org/download/) или [DBeaver](https://dbeaver.io/).

**Рекомендуем менять данные ТОЛЬКО через интерфейс Admin панели или сам сайт, изменение данных в БД через сторонние ресурсы может все поломать**
