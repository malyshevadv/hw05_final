# Бекенд для социальной сети блогеров (hw05_final, часть yatube_project)

### Описание
Финальный проект по созданию сайта блогов с подпиской на авторов.

1. В проект добавлены кастомные страницы ошибок:
- 404 page_not_found
- 403 permission_denied_view
- Написан тест, проверяющий, что страница 404 отдает кастомный шаблон.
2. С помощью sorl-thumbnail выведены иллюстрации к постам:
- в шаблон главной страницы,
- в шаблон профайла автора,
- в шаблон страницы группы,
- на отдельную страницу поста.
- Написаны тесты, которые проверяют:
  - при выводе поста с картинкой изображение передаётся в словаре context
    - на главную страницу,
    - на страницу профайла,
    - на страницу группы,
    - на отдельную страницу поста;
  - при отправке поста с картинкой через форму PostForm создаётся запись в базе данных;
3. Создана система комментариев
- Написана система комментирования записей. На странице поста под текстом записи выводится форма для отправки комментария, а ниже — список комментариев. Комментировать могут только авторизованные пользователи. Работоспособность модуля протестирована.
4. Кеширование главной страницы
- Список постов на главной странице сайта хранится в кэше и обновляется раз в 20 секунд.
5. Тестирование кэша
- Написан тест для проверки кеширования главной страницы.
6. Реализована систему подписки на авторов и ленту постов подписок.
- Создана модель, view-функция, шаблоны.
- Написаны тесты, проверяющие работу системы:
  - Авторизованный пользователь может подписываться на других пользователей и удалять их из подписок.
  - Новая запись пользователя появляется в ленте тех, кто на него подписан и не появляется в ленте тех, кто не подписан.

### Технологии
- Python 3.7
- Django 2.2.19
### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- В папке с файлом manage.py выполните команду:
```
python3 manage.py runserver
```

Выполнение тестов:
```
python manage.py test
```
### Авторы
Дарья М.
