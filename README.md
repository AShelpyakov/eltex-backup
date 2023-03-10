#  eltex backup
### Описание
Скрипт для сохранения конфигурации маршрутизаторов Eltex ESR. Программа сохраняет конфигурацию оборудования в указаннную
папку, высылает список проблемного оборудования и разницу в конфигурациях на почту. Есть возможность удалять лишние
строчки, заменять части строк. 
### Технологии
Python 3.7,
GitPython 3.1.30,
nornir 3.3.0,
nornir-netmiko 0.2.0,
nornir-utils 0.2.0.
### Запуск проекта
- Склонировать репозиторий с GitHub.
- Установить виртуальное окружение и зайти в него(опционально)
```
# Создаем. Одна из команд, зависит от ОС.
python -m venv env
python3 -m venv env
# Заходим в окружение
source ./env/bin/activate
```
- Установить необходимые python библиотеки:
```
pip install -r requirements.txt
```
- Внести изменения в config.yaml. Минимально изменить настройки smtp, поддерживается только SMTPS.
- Заполнить yaml файлы в inventory. Вся логика взята из Nornir.
- Запустить скрипт.
```
python main.py
```
### Комментарии к конфигурации
```
  data:
    backup_commands:  # список команд, вывод которых мы хотим сохранить.
    delete_patterns:  # паттерны строк которые мы не хотим видеть сохраненными, в примере фильтруются логирование команд.
    change_arguments: # паттерны субстрок которые нужно заменить, в примере стираем пароли.
    last_command:     # костыль что бы определить конец сохраняемых комманд
```
### Автор
Александр Шельпяков