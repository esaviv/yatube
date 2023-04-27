# Yatube
### Описание
Социальная сеть блогеров. В ней пользователи могут создать учетную запись, публиковать записи, подписаться на любимых авторов и отмечать понравившиеся записи.
### Технологии
Python 3.9, Django 2.2.19, Pillow 8.3.1
### Автор
esaviv
## Как запустить проект в dev-режиме:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/esaviv/yatube.git
```
```
cd yatube
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv venv | python -m venv venv
```
```
source env/bin/activate | source venv/Scripts/activate
```
```
python3 -m pip install --upgrade pip | python -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
Выполнить миграции:
```
python3 yatube/manage.py migrate | python yatube/manage.py migrate
```
Запустить проект:
```
python3 yatube/manage.py runserver | python yatube/manage.py runserver
```
