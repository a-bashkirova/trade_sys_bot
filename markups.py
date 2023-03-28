from telebot import types

company_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
gazp = types.KeyboardButton("Газпром")
yand = types.KeyboardButton("Яндекс")
aero = types.KeyboardButton("Аэрофлот")
sber = types.KeyboardButton("Сбербанк")
company_markup.add(gazp, yand, aero, sber)

default_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
back = types.KeyboardButton("Назад")
default_markup.add(back)
