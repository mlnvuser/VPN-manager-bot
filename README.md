Вы можете использовать данный Telegram-bot если развернули OpenVPN на своём сервере.
В проекте два главных файла:
-traffic_file.py - можно запустить при помощи планировщика задач crontab в Linux (например один раз в минуту). Отслеживает изменения log-файла status.log, который находится по пути "/var/log/openvpn/status.log";
-botVPN - запускает Telegram-бот и обрабатывает определенные команды (статистика за месяц, дату, период, показ активных пользователей, их трафик, отправка сгенерированной VPN конфигурации для администраторов).
Проверьте правильность переменных: bot, database, file_path.
