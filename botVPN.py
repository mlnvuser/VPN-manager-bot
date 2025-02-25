#!/usr/bin/env python3
import telebot, subprocess, os
from functions import convert_bytes, get_users, is_valid_date, reverse_date_format, year_by_month, is_valid_input, check_password

bot = telebot.TeleBot('') # API
database = 'database.db'
user_states = {}
months = {
    "Декабрь":'12', "Январь":'01', "Февраль":'02', "Март":'03',
     "Апрель":'04', "Май":'05', "Июнь":'06', "Июль":'07',
     "Август":'08', "Сентябрь":'09', "Октябрь":'10', "Ноябрь":'11'
}

#message_handler - декоратор
@bot.message_handler(commands=['start']) #При вводе /start
def main(message): #message - хранит в себе всю инф. о пользователе
    bot.send_message(message.chat.id, text='Используйте команду /help для просмотра возможностей бота!')


@bot.message_handler(commands=['help']) #При вводе /help
def help(message):
    bot.send_message(message.chat.id, text='Здесь будет справочная информация по возможностям бота...')


@bot.message_handler(commands=['active']) #При вводе /active - показать подключенных пользователей
def active_users(message):
    users = get_users(mode='active', database=database)
    if len(users) == 0:
      bot.reply_to(message, text='Активных пользователей нет.')
    else:
      text = 'Список подключенных к VPN пользователей: \n'
      i = 1
      for key, value in users.items():
          text += f"{i}) Имя: {key} | Трафик: {convert_bytes(value['total_traffic'])} | Дата и время подключения: {value['connection_date']} {value['connection_time']}\n"
          i += 1
      bot.reply_to(message, text=text)


@bot.message_handler(commands=['date']) #При вводе /date- показать трафик пользователей за определенную дату
def ask_date(message): #В случае запроса статистики за определенную дату
    # Отправляем сообщение с просьбой ввести дату
    msg = bot.send_message(message.chat.id, "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ: ")
    bot.register_next_step_handler(msg, process_date) #Ждём ввода даты от пользователя


# Функция для обработки введенной даты
def process_date(message):
    text = message.text
    if is_valid_date(text): #Если формат даты верный
        date = reverse_date_format(text) #Преобразуем в новый формат для поиска в БД
        users = get_users(mode='date', database=database, target_date=date)
        text = f'Статистика пользователей за {text}:\n'
        i = 1
        for key, value in users.items():
            text += f'{i}) Имя: {key} | Трафик: {convert_bytes(value)}\n'
            i += 1
        if len(users) == 0:
            text = f'За {message.text} статистика отсутствует.'
        bot.reply_to(message, text=text)
    else:
        bot.send_message(message.chat.id, "Введён неправильный формат даты.")


@bot.message_handler(commands=['month']) #Статистика пользователей за месяц;
def stat_month(message):

    # Создание Inline клавиатуры
    markup = telebot.types.InlineKeyboardMarkup()

    # Добавление кнопок с месяцами в 3 строки по 4 элемента
    list_months = list(months.keys())
    for i in range(0, len(list_months), 3):
        row = []
        for month in list_months[i:i + 3]:
            button = telebot.types.InlineKeyboardButton(month, callback_data=month)
            row.append(button)
        markup.add(*row)

    bot.send_message(message.chat.id, "Выберите месяц:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in months) #После выбора месяца отправляет запрос на предоставление сведений;
def handle_month_selection(call):
    bot.answer_callback_query(call.id)  # Это нужно для удаления загрузки
    users = get_users(mode='period', database=database, start_period=f'{year_by_month(months[call.data])}-{months[call.data]}-01',
                      end_period=f'{year_by_month(months[call.data])}-{months[call.data]}-31')
    text = f'Статистика пользователей за {call.data} {year_by_month(months[call.data])}:\n'
    i = 1
    if len(users) == 0:
        bot.send_message(call.message.chat.id,
                         text=f'Статистика пользователей за {call.data} {year_by_month(months[call.data])} отсутствует.')
    else:
        for key, value in users.items():
            text += f'{i}) Имя: {key} | Трафик: {convert_bytes(value)}\n'
            i += 1
        bot.send_message(call.message.chat.id, text=text)


@bot.message_handler(commands=['period']) #Статистика пользователей за период;
def stat_period(message):
    msg = bot.send_message(message.chat.id, "Введите начальную дату в формате ДД.ММ.ГГГГ: ")
    bot.register_next_step_handler(msg, process_start_period)  # Ждём ввода начала периода от пользователя

def process_start_period(message):
    start_date = message.text
    if is_valid_date(start_date):
        bot.send_message(message.chat.id, "Введите конечную дату в формате ДД.ММ.ГГГГ: ")
        bot.register_next_step_handler(message, process_end_period, start_date)
    else:
        bot.send_message(message.chat.id, "Введен неверный формат даты.")

def process_end_period(message, start_date):
    end_date = message.text
    if is_valid_date(end_date):
        users = get_users(mode='period', database=database,
                          start_period=f'{reverse_date_format(start_date)}',
                          end_period=f'{reverse_date_format(end_date)}')
        text = f'Статистика пользователей с {start_date} по {end_date}:\n'
        i = 1
        if len(users) == 0:
            bot.send_message(message.chat.id,
                             text=f'Статистика пользователей с {start_date} по {end_date} отсутствует.')
        else:
            for key, value in users.items():
                text += f'{i}) Имя: {key} | Трафик: {convert_bytes(value)}\n'
                i += 1
            bot.send_message(message.chat.id, text=text)
    else:
        bot.send_message(message.chat.id, "Введен неверный формат даты.")


@bot.message_handler(commands=['vpn']) #При вводе /vpn
def vpn(message):
    # Создание Inline клавиатуры
    markup = telebot.types.InlineKeyboardMarkup()

    btn1 = telebot.types.InlineKeyboardButton('Создать пользователя', callback_data='create')
    btn2 = telebot.types.InlineKeyboardButton('Удалить пользователя', callback_data='delete')
    markup.row(btn1,btn2)

    bot.send_message(message.chat.id, "Что необходимо сделать?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['create', 'delete'])
def name_client(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "Введите пароль администратора:")
    user_states[call.message.chat.id] = "waiting_for_admin_pass"
    bot.register_next_step_handler(msg, admin_check, call.data)

def admin_check(message, callback_data): #Проверяем является ли пользователь администратором
    if check_password(message.text,'admin.json'):
        if callback_data == 'create':
            msg = bot.send_message(message.chat.id, "Напишите имя клиента:")
            user_states[message.chat.id] = "waiting_for_client_name"
            bot.register_next_step_handler(msg, create_user)
        elif callback_data == 'delete':
            bot.send_message(message.chat.id, "Удаление пользователей временно не предусмотрено!")
    else:
        bot.send_message(message.chat.id, "Неверный пароль!")
        del user_states[message.chat.id]


def create_user(message):
    chat_id = message.chat.id

    if chat_id in user_states and user_states[chat_id] == "waiting_for_client_name":
        unsanitized_client = message.text

        if is_valid_input(unsanitized_client):
            try:
                process = subprocess.Popen('./openvpn-install.sh', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate(input=f'1\n{unsanitized_client}\n1\n')  # Пример ввода, если скрипт ожидает эти данные
                error = 'The specified client CN was already found in easy-rsa, please choose another name.'

                if error in stdout:
                    bot.send_message(chat_id,
                                     "Пользователь с таким именем уже существует!")
                else:
                    if os.path.exists(f"/root/{unsanitized_client}.ovpn"):
                        with open(f"/root/{unsanitized_client}.ovpn", 'rb') as ovpn_file:
                            bot.send_document(chat_id, ovpn_file, caption="Ваш файл:")
                    else:
                        bot.send_message(chat_id,
                                         "Ошибка открытия файла!")
            except Exception as e:
                bot.send_message(chat_id, f"Произошла ошибка: {str(e)}")

            del user_states[chat_id]

        else:
            bot.send_message(chat_id,
                             "Ошибка: Ввод содержит недопустимые символы. Пожалуйста, используйте только буквы, цифры и символы подчеркивания.")


# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)