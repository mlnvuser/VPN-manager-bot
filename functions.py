import sqlite3, re, hashlib, json
from datetime import datetime


def check_password(input_password, json_file):
    # Вычисляем хэш от введенного пароля
    input_hash = hashlib.sha256(input_password.encode()).hexdigest()

    # Открываем файл admin.json и загружаем данные
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Сравниваем хэши
    if input_hash == data.get('pass'):
        return True


def is_valid_input(user_input):
    """Проверяет, что ввод пользователя не содержит специальных символов или команд."""
    pattern = r'^[a-zA-Z0-9_ ]+$'

    if re.match(pattern, user_input):
        return True
    else:
        return False


def convert_date_format(date_str):
    # Парсим строку в формате "Tue Jan 28 17:34:40 2025"
    dt_object = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")

    # Преобразуем в новый формат
    date = dt_object.strftime("%Y-%m-%d")
    time = dt_object.strftime("%H:%M:%S")

    return date,time


def reverse_date_format(date):
    # Преобразование строки в объект datetime
    date_obj = datetime.strptime(date, '%d.%m.%Y')
    # Форматирование объекта datetime в строку нужного формата
    return date_obj.strftime('%Y-%m-%d')


def year_by_month(month): #Пример ввода месяца - "01" - str
    '''Определяет какой вернуть год по введенному месяцу'''

    month_now = int(datetime.today().strftime(format='%m'))
    year_now = int(datetime.today().strftime(format='%Y'))
    if int(month) > month_now:
        return str(year_now-1)
    else:
        return str(year_now)


def convert_bytes(size_in_bytes):
    # Определяем единицы измерения
    units = ["B", "KB", "MB", "GB", "TB", "PB"]

    # Начинаем с байтов
    unit_index = 0

    # Переводим в более крупные единицы, пока размер больше 1024
    while size_in_bytes >= 1024 and unit_index < len(units) - 1:
        size_in_bytes /= 1024
        unit_index += 1

    # Форматируем результат с двумя знаками после запятой
    return f"{size_in_bytes:.2f} {units[unit_index]}"


def is_valid_date(date_str): #Проверка введенного формата даты
    try:
        # Пытаемся преобразовать строку в объект datetime
        datetime.strptime(date_str, '%d.%m.%Y')
        return True
    except ValueError:
        # Если возникает ошибка, значит дата некорректна
        return False


def get_users(mode,database,target_date=None,start_period=None,end_period=None):
    # Вернёт список активных пользователей подключенных к серверу
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    if mode == 'active':
        cursor.execute('''
            SELECT username, received_traffic, sent_traffic, connection_date, connection_time
            FROM connections
            WHERE disconnection_date IS NULL AND disconnection_time IS NULL
            ''')
    elif mode == 'date':
        cursor.execute('''
            SELECT username, SUM(received_traffic) AS total_received, SUM(sent_traffic) AS total_sent
            FROM connections
            WHERE connection_date = ?
            GROUP BY username;
            ''', (target_date,))
    elif mode == 'period':
        cursor.execute('''
            SELECT username, SUM(received_traffic) AS total_received, SUM(sent_traffic) AS total_sent
            FROM connections
            WHERE connection_date >= ? AND connection_date <= ?
            GROUP BY username;
            ''', (start_period,end_period))

    # Получаем результаты
    results = cursor.fetchall()

    # Формируем выходные данные
    output = {}
    if mode == 'active':
        for row in results:
            user = {}
            username, received_traffic, sent_traffic, connection_date, connection_time = row
            total_traffic = received_traffic + sent_traffic
            user['total_traffic'] = total_traffic
            user['connection_date'] = connection_date
            user['connection_time'] = connection_time
            output[username] = user
    else:
        for row in results:
            username, received_traffic, sent_traffic = row
            total_traffic = received_traffic + sent_traffic
            output[username] = total_traffic

    # Закрываем соединение с базой данных
    conn.close()

    return output
