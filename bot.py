from telebot import types, TeleBot
from constants import WELCOME_MSG, ABOUT_MSG, map_companies, TOKEN
import dateparser
import requests
import json
from markups import company_markup
from utils import User

bot = TeleBot(TOKEN)
user_dict = {}


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, WELCOME_MSG)


@bot.message_handler(commands=["about"])
def about_message(message):
    bot.send_message(message.chat.id, ABOUT_MSG)


@bot.message_handler(commands=["predict"])
def predict(message):
    msg = bot.send_message(message.chat.id, "Для акций какой компании ты хочешь получить прогноз?",
                           reply_markup=company_markup)
    user_dict[message.chat.id] = User(message.chat.id)
    bot.register_next_step_handler(msg, ask_company)


def ask_company(message):
    text = message.text
    if text.lower() not in ['газпром', 'яндекс', 'аэрофлот']:
        msg = bot.send_message(message.chat.id, "Неправильное название компании. Попробуй еще раз",
                               reply_markup=company_markup)
        bot.register_next_step_handler(msg, ask_company)
    user_dict[message.chat.id].company = map_companies[text.lower()]
    dates = requests.post('http://localhost:8080/get_dates',
                          data=json.loads(json.dumps({"company": map_companies[text.lower()]})))
    l, r = dates.json()["dates"].split('/')
    msg = bot.send_message(message.chat.id, f"Введи, пожалуйста, дату, на которую ты хочешь получить прогноз в формате ДД.ММ.ГГГГ.\nДопустимый диапазон дат для акций {text.capitalize()}: от {l} до {r}")
    bot.register_next_step_handler(msg, ask_date)


def ask_date(message):
    text = message.text
    date = dateparser.parse(text)
    if date is None:
        msg = bot.send_message(message.chat.id, "Неправильный формат даты. Попробуй еще раз")
        bot.register_next_step_handler(msg, ask_date)
    req_date = f"{date.day}/{date.month}/{date.year}"
    company = user_dict[message.chat.id].company
    data = {
        "rq_id": "1",
        "company": company,
        "req_date": req_date,
    }
    res = requests.post('http://localhost:8080/predict', data=json.loads(json.dumps(data)))
    if res.json()['flg'] == 1:
        bot.send_message(message.chat.id, f"Акции {company.capitalize()} {req_date} *вырастут*\nВведи новую дату или команду /predict, чтобы выбрать другую компанию", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"Акции {company.capitalize()} {req_date} *упадут*\nВведи новую дату или команду /predict, чтобы выбрать другую компанию", parse_mode="Markdown")


@bot.message_handler(content_types=["text"])
def text_message(message):
    bot.send_message(message.chat.id, "Я не знаю такой команды :(\nПопробуй еще раз, пожалуйста")


bot.infinity_polling()
