import os, sqlite3, traceback
from datetime import datetime
from functions import convert_date_format

def main(file_path):
    try:
        # Проверяем, существует ли файл базы данных, и создаем его, если нет
        if not os.path.exists('database.db'):
            open('database.db', 'w').close()

        # Подключаемся к базе данных
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Создаем таблицу Connections, если она еще не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                received_traffic INTEGER NOT NULL,
                sent_traffic INTEGER NOT NULL,
                connection_date DATE NOT NULL,
                connection_time TIME NOT NULL,
                disconnection_date DATE,
                disconnection_time TIME
            )
        ''')

        # Открываем файл c подключенными пользователями для чтения
        with open(file_path, 'r') as file:
            usernames_in_server = {}  # Словарь для хранения имен пользователей их даты и времени подключения из файла
            for i in range(3): # Таблица с пользователями начинается с 3-ей строки файла
                next(file) #Используем функцию-генератор

            for line in file:
                # Проверяем, не достигли ли мы строки "ROUTING TABLE"
                if line.strip() == "ROUTING TABLE":
                    break

                # Разделяем строку на части
                parts = line.strip().split(',')
                if len(parts) < 5:
                    continue  # Пропускаем строки с недостаточным количеством данных
                if parts[0] == 'UNDEF':
                    continue

                username, ip_address, received_traffic, sent_traffic, connection_start = parts
                connection_date,connection_time = convert_date_format(connection_start)
                usernames_in_server[username] = [connection_date,connection_time] # Добавляем имя пользователя, дату и время его подключения в словарь

                # Проверяем, существует ли запись с таким именем пользователя и временем подключения
                cursor.execute('''
                    SELECT received_traffic, sent_traffic FROM Connections
                    WHERE username = ? AND connection_date = ? AND connection_time = ?
                ''', (username, connection_date, connection_time))

                result = cursor.fetchone()

                if result is None:
                    # Если записи нет, добавляем новую
                    cursor.execute('''
                        INSERT INTO Connections (username, ip_address, received_traffic, sent_traffic, connection_date, connection_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (username, ip_address, received_traffic, sent_traffic, connection_date, connection_time))
                else:
                    # Если запись существует, проверяем и обновляем данные о трафике, если они изменились
                    db_received_traffic, db_sent_traffic = result
                    if db_received_traffic != received_traffic or db_sent_traffic != sent_traffic:
                        cursor.execute('''
                            UPDATE Connections
                            SET received_traffic = ?, sent_traffic = ?
                            WHERE username = ? AND connection_date = ? AND connection_time = ?
                        ''', (received_traffic, sent_traffic, username, connection_date, connection_time))

            # Проверяем пользователей, которые есть в базе и у которых пустые дата и время отключения
            cursor.execute('''
                SELECT username, connection_date, connection_time FROM Connections
                WHERE disconnection_date IS NULL AND disconnection_time IS NULL
            ''')
            rows = cursor.fetchall()
            for row in rows:
                username, connection_date, connection_time = row
                if username not in usernames_in_server or usernames_in_server[username] != [connection_date,connection_time]:
                    # Если пользователь отсутствует в файле и у него пустые поля disconnection_date и time,
                    # устанавливаем текущие дату и время в эти поля
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    current_time = datetime.now().strftime('%H:%M:%S')
                    cursor.execute('''
                        UPDATE Connections
                        SET disconnection_date = ?, disconnection_time = ?
                        WHERE username = ? AND connection_date = ? AND connection_time = ?
                    ''', (current_date, current_time, username, connection_date, connection_time))

        # Сохраняем изменения и закрываем соединение
        conn.commit()
        conn.close()
    except:
        print(f'{datetime.today().strftime('%d.%m.%Y %H:%M:%S')} - error:\n')
        traceback.print_exc()
    else:
        print(f'{datetime.today().strftime('%d.%m.%Y %H:%M:%S')} - successfully;')


if __name__ == "__main__":
    main("status.log")