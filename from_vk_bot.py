import telebot


class signal_sender():
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)

    # Обработчик команды /sendmessage
    @bot.message_handler(commands=['sendmessage'])
    def send_message(message):
        # Отправка сообщения пользователю, который вызвал команду
        self.bot.reply_to(message, 'Привет! Это сообщение отправлено по команде /sendmessage.')

    # Основная функция для запуска бота
    def main():
        # Запуск бота
        bot.polling(none_stop=True)

