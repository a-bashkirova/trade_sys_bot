from telebot import types, TeleBot
from constants import WELCOME_MSG, ABOUT_MSG, MAP_COMPANIES, TOKEN, RESULT_FLG, REVERSE_MAP_COMPANIES
import dateparser
import requests
import json
from markups import company_markup, default_markup
from utils import User

bot = TeleBot(TOKEN)
user_dict = {}


def health():
    return requests.get('http://localhost:8080/health')


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, WELCOME_MSG)


@bot.message_handler(commands=["about"])
def about_message(message):
    bot.send_message(message.chat.id, ABOUT_MSG)


@bot.message_handler(commands=["predict"])
def predict(message):
    user_dict[message.chat.id] = User(message.chat.id)
    msg = bot.send_message(message.chat.id, "Для акций какой компании ты хочешь получить прогноз?",
                           reply_markup=company_markup)
    bot.register_next_step_handler(msg, ask_company)


def ask_company(message):
    text = message.text
    if text.lower() not in ['газпром', 'яндекс', 'аэрофлот', 'сбербанк']:
        msg = bot.send_message(message.chat.id, "Неправильное название компании. Попробуй еще раз",
                               reply_markup=company_markup)
        bot.register_next_step_handler(msg, ask_company)
    user_dict[message.chat.id].company = MAP_COMPANIES[text.lower()]
    dates = requests.post('http://localhost:8080/get_dates',
                          data=json.loads(json.dumps({"company": MAP_COMPANIES[text.lower()]})))
    l, r = dates.json()["dates"].split('/')
    user_dict[message.chat.id].min_date, user_dict[message.chat.id].max_date = dateparser.parse(l), dateparser.parse(r)
    msg = bot.send_message(message.chat.id, f"Введи, пожалуйста, дату, на которую ты хочешь получить прогноз в формате ДД.ММ.ГГГГ.\nДопустимый диапазон дат для акций {text.capitalize()}: от {l} до {r}",
                           reply_markup=default_markup)
    bot.register_next_step_handler(msg, ask_date)


def ask_date(message):
    text = message.text
    if text.lower() == 'назад':
        msg = bot.send_message(message.chat.id, "Для акций какой компании ты хочешь получить прогноз?",
                               reply_markup=company_markup)
        bot.register_next_step_handler(msg, ask_company)
    else:
        date = dateparser.parse(text)
        if date is None:
            msg = bot.send_message(message.chat.id, "Неправильный формат даты. Попробуй еще раз",
                                   reply_markup=default_markup)
        elif date < user_dict[message.chat.id].min_date or date > user_dict[message.chat.id].max_date:
            msg = bot.send_message(message.chat.id, "Указанная дата не помещается в диапазон. Попробуй еще раз",
                                   reply_markup=default_markup)
        else:
            req_date = f"{date.year}-{date.month}-{date.day}"
            company = user_dict[message.chat.id].company
            data = {
                "rq_id": "1",
                "company": company,
                "req_date": req_date,
            }
            res = requests.post('http://localhost:8080/predict', data=json.loads(json.dumps(data)))
            res_flg = res.json()['flg']
            msg = bot.send_message(message.chat.id, f"Акции {REVERSE_MAP_COMPANIES[company]} {req_date} {RESULT_FLG[res_flg]}\nВведи новую дату или нажми 'Назад', чтобы выбрать другую компанию",
                                   parse_mode="Markdown", reply_markup=default_markup)
        bot.register_next_step_handler(msg, ask_date)


@bot.message_handler(content_types=["text"])
def text_message(message):
    bot.send_message(message.chat.id, "Я не знаю такой команды :(\nПопробуй еще раз, пожалуйста")


bot.infinity_polling()
