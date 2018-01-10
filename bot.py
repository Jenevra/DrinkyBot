import config
import telebot
import os
import socket
import psycopg2
import re
from telebot import types

print('hello')

# create object bot
bot = telebot.TeleBot(config.token)


@bot.message_handler(content_types=['text'])
def send_message(message):
    bot.send_message(message.chat.id, message.text)


sock = socket.socket()
sock.bind(('', int(os.environ.get('PORT', '5000'))))
sock.listen(1)

if __name__ == '__main__':
    bot.polling(none_stop=True)
