#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

import requests
import telebot

import config

TOKEN = config.TOKEN
APP_ID = config.APP_ID

bot = telebot.TeleBot(TOKEN)
url = "https://openexchangerates.org/api/latest.json?app_id=" + APP_ID

keys = {
    'Бобруйский серебряник. Для ввода: боб или bob': 'BOB',
    'Евро. Для ввода: евро или eur': 'EUR',
    'Китайский юань. Для ввода: юань или cny': 'CNY',
    'Российский рубль. Для ввода: руб или rub': 'RUB',
}


class ConvertException(Exception):
    pass


# Обрабатываются все сообщения, содержащие команды '/start' or '/help'.
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: telebot.types.Message):
    text = "Я конвертирую валюту. Для работы введите команду в формате:" \
           "\n<Количество вашей валюты>" \
           "\n<Наименование вашей валюты>" \
           "\n<В какую валюту хотите перевести>" \
           "\nНапример, для перевода 1000 руб. в юани введите через пробел:" \
           "\n1000 руб юань" \
           "\nСписок доступных валют: /values"

    username = message.chat.username
    if username is not None:
        bot.reply_to(message, f"Привет, @{username}!")
    else:
        bot.reply_to(message, "Привет!")

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['values'])
def values(message: telebot.types.Message):
    text = "СПИСОК ДОСТУПНЫХ ВАЛЮТ:"
    for key in keys.keys():
        text += f"\n- {key}"
    bot.send_message(message.chat.id, text)


def get_currency(val, position=None):
    if isinstance(val, str) and position != 1:
        if val.upper() in ["РУБ", "RUB"]:
            return "RUB"
        elif val.upper() in ["ЕВРО", "EUR"]:
            return "EUR"
        elif val.upper() in ["ЮАНЬ", "CNY"]:
            return "CNY"
        elif val.upper() in ["БОБ", "BOB"]:
            return "BOB"
        elif val.upper() in ["ДОЛЛАР", "USD"]:
            return "USD"
        else:
            response_user = f"Ошибка при вводе <* {val} *> в позиции № {position}! " \
                            f"\nВведите валюту из списка!" \
                            f"\nСписок доступных валют: /values"

            return False, response_user

    elif val and position == 1:
        try:
            val_int = float(val.replace(",", "."))
            if isinstance(val_int, (int, float)) and position == 1:
                return val_int
        except ValueError:
            response_user = f"Ошибка при вводе <* {val} *> в позиции № {position}! \
            Введите число - количество переводимой валюты!"
            return False, response_user


@bot.message_handler(content_types=['text', ])
def convert(message: telebot.types.Message):
    amount = 1  # Количество переводимой валюты по умолчанию
    result_start_currency = None
    result_end_currency = None
    start_currency = None
    end_currency = None
    let = False

    response = requests.get(url)
    data = response.json()
    base = float(data['rates']["USD"])

    # Преобразуем timestamp в объект datetime
    timestamp = data['timestamp']
    date = datetime.datetime.fromtimestamp(timestamp)

    # Разбиваем сообщение пользователя и обрабатываем ошибки
    user_message = message.text.split(" ")

    try:
        if len(user_message) == 3:
            amount = get_currency(user_message[0], 1)
            if isinstance(amount, (int, float)):
                let = True
            else:
                bot.send_message(message.chat.id, amount[1])
                return False

            start_currency = get_currency(user_message[1], 2)
            if isinstance(start_currency, str):
                result_start_currency = data['rates'][start_currency]
                let = True
            else:
                bot.send_message(message.chat.id, start_currency[1])
                return False

            end_currency = get_currency(user_message[2], 3)
            if isinstance(end_currency, str):
                result_end_currency = data['rates'][end_currency]
                let = True
            else:
                bot.send_message(message.chat.id, end_currency[1])
                return False

        if len(user_message) < 3:
            raise ConvertException("Введите три параметра через пробел, например: 1000 руб юань")

        if len(user_message) > 3:
            raise ConvertException("Введено больше трёх параметров.")

        if start_currency == end_currency:
            raise ConvertException("Введены одинаковые валюты.")

    except ConvertException as e:
        bot.send_message(message.chat.id, str(e))

    if let:
        course = (base / float(result_start_currency)) / (base / float(result_end_currency)) * amount
        round_course = round(course, 3)
        total_course = f"За {amount} {start_currency} Вы получите {round_course} {end_currency}.\nЦена курса на {date}"
        bot.send_message(message.chat.id, total_course)


bot.polling(none_stop=True)  # Старт
