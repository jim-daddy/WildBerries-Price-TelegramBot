# импорты
import time
import validators
import sqlite3

import telebot
from telebot import types
from threading import Thread

import config
from WildBerries import WildBerries
from reserved_rep import replaceSymbol

bot = telebot.TeleBot(config.API_TOKEN)

PRODUCTS = 'db/products.db'
USERS = 'db/users.db'

product_user_id = None
product_title = None
product_price = None
selected_price = None
product_url = None
delete_message = None


# Бесконечный цикл для проверки цены
def main_cycle():
    try:
        while True:
            start_time = time.time()

            connection = sqlite3.connect(PRODUCTS)
            cursor = connection.cursor()

            cursor.execute('SELECT * FROM Products')
            products = cursor.fetchall()

            for product in products:
                print(product)
                user_id = product[1]
                users_price = int(product[4])
                saved_price = int(product[3])
                url = product[5]

                wildberries = WildBerries(url)

                html = wildberries.get_html()
                if html:
                    try:
                        parse = wildberries.parse_data()

                        title = parse['h1']
                        sku = parse['sku']
                        price = int(parse['price'])
                        brand = replaceSymbol(parse['brand'])
                        image = parse['image']

                        if users_price >= price:
                            link = f'[• *{brand} / {replaceSymbol(title)}*]({url})'
                            bot.send_photo(user_id, image,
                                           f'Название:\n{link}\n\n'
                                           f'Артикул: • __{sku}__\n'
                                           f'Бренд: • __{brand}__\n\n'
                                           f'🔥*Снижение цены*🔥:\n • {str(price)} ₽  _~{str(saved_price)} ₽~_\n\n'
                                           f'_«Цена указана без индивидуальной скидки, окончательная '
                                           f'сумма зависит от Вашей личной скидки в ЛК WildBerries»_',
                                           parse_mode='MarkdownV2')

                            cursor.execute('DELETE FROM Products WHERE id = ?', (product[0],))
                            cursor.execute("UPDATE Products SET id = id - 1 WHERE id > ?", (product[0],))
                            connection.commit()

                    except Exception as e:
                        print(e)
                else:
                    print(f"Ссылка на товар не рабочая:\n(user: {product[1]}, product: {product[2]})")
            connection.close()

            end_time = time.time()
            work_time = end_time - start_time

            if 300 - work_time > 0:
                time.sleep(300 - work_time)
    except Exception as e:
        print(e)
        print("Работа программы прекратилась!")


# запуск main_cycle асинхронно
thread = Thread(target=main_cycle)
thread.start()


# message_handler для удаления товара из Базы Данных
@bot.message_handler(commands=['delete'])
def choose_delete(message):
    try:
        connection = sqlite3.connect(PRODUCTS)
        cursor = connection.cursor()

        cursor.execute("SELECT title FROM Products WHERE user_id = ?",
                       (message.from_user.id,))
        products = cursor.fetchall()

        if not products:
            bot.send_message(message.chat.id, f'*У вас пока нет добавленных товаров.*\n'
                                              f'Это можно сделать с помощью команды /start', parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "📌*СПИСОК ВАШИХ ТОВАРОВ:*", parse_mode='Markdown')
            for product in products:
                bot.send_message(message.chat.id, f"{product[0]}")

            # создаем клавиатуру
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)

            button = types.KeyboardButton(text="Отмена❌")
            keyboard.add(button)

            bot.send_message(message.chat.id, "_«Напишите *ПОЛНОЕ* название товара, чтобы удалить его»_",
                             reply_markup=keyboard,
                             parse_mode='MarkdownV2')
            bot.register_next_step_handler(message, delete)
        connection.close()

    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Упс! Что-то пошло не так!")


# Функция удаления
def delete(message):
    global delete_message

    try:
        if message.text == "Отмена❌":
            bot.send_message(message.chat.id, 'Процесс отменен👍')
        else:
            product_name = message.text

            connection = sqlite3.connect(PRODUCTS)
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM Products WHERE user_id = ? AND title = ?",
                           (message.from_user.id, product_name))
            product = cursor.fetchone()
            if not product:
                # создаем клавиатуру
                keyboard = types.InlineKeyboardMarkup()

                button1 = types.InlineKeyboardButton(text="Да", callback_data="delete_yes")
                button2 = types.InlineKeyboardButton(text="Нет", callback_data="cancel")
                keyboard.add(button1, button2)

                delete_message = bot.send_message(message.chat.id, "*У вас нет товара с таким названием, "
                                                                   "либо вы написали название не полностью!*",
                                                  reply_markup=types.ReplyKeyboardRemove(), parse_mode='Markdown')
                bot.send_message(message.chat.id, "Хотите выбрать другой товар для удаления?",
                                 reply_markup=keyboard, parse_mode='Markdown')
            else:
                id_ = product[0]
                cursor.execute('DELETE FROM Products WHERE user_id = ? AND title = ?',
                               (message.from_user.id, product_name))
                cursor.execute("UPDATE Products SET id = id - 1 WHERE id > ?", (id_,))
                connection.commit()

                bot.send_message(message.chat.id, "🗑Товар успешно удален!", reply_markup=types.ReplyKeyboardRemove())

            connection.close()
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Упс! Что-то пошло не так!", reply_markup=types.ReplyKeyboardRemove())


# Запуск при любом сообщении
@bot.message_handler(content_types=['text'])
def send_welcome(message):
    try:
        if validators.url(message.text):
            link_request(message)
        else:
            flag = True
            connection = sqlite3.connect(USERS)
            cursor = connection.cursor()

            cursor.execute('SELECT * FROM Users')
            users = cursor.fetchall()
            for user in users:
                if user[0] == message.from_user.id:
                    flag = False
                    break
            connection.close()

            # создаем клавиатуру
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)

            button = types.KeyboardButton(text="Отмена❌")
            keyboard.add(button)

            if flag:
                url_text = (f'[Ссылка на официальный сайт интернет-магазина WildBerries]('
                            f'https://www.wildberries.ru/catalog)')

                bot.send_message(message.chat.id,
                                 f'Здравствуйте, {message.from_user.first_name}!'
                                 f'\n\nЯ - бот, который мониторит цены на товары. '
                                 f'\nДля этого скопируйте и вставьте сюда ссылку'
                                 f' на продукт с сайта интернет-магазина WildBerries.'
                                 f'\n{url_text}',
                                 reply_markup=keyboard,
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, link_request)
            else:
                url_text = f'[WildBerries](https://www.wildberries.ru)'
                bot.send_message(message.chat.id, f'Скопируйте и вставьте сюда ссылку на '
                                                  f'товар с сайта интернет-магазина {url_text}',
                                 reply_markup=keyboard,
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, link_request)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, '😵‍💫Упс! Возникла непредвиденная ошибка')


# Запрос ссылки на товар и ее проверка
def link_request(message):
    global product_title, product_url, product_price

    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, 'Процесс отменен👍')
    else:
        search_message = bot.send_message(message.chat.id,
                                          '🕵‍Борозжу просторы WildBerries в поисках товара...',
                                          parse_mode='Markdown', reply_markup=types.ReplyKeyboardRemove())

        # создаем клавиатуру
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)

        button = types.KeyboardButton(text="Отмена❌")
        keyboard.add(button)

        try:
            url = message.text
            wildberries = WildBerries(url)

            html = wildberries.get_html()
            if html:
                parse = wildberries.parse_data()

                title = parse['h1']
                sku = parse['sku']
                price = parse['price']
                old_price = parse['old_price']
                brand = replaceSymbol(parse['brand'])
                image = parse['image']

                product_title = title
                product_url = url
                product_price = price

                bot.delete_message(message.chat.id, search_message.message_id)

                bot.send_photo(message.chat.id, image,
                               f'Название:\n• *{brand} / {replaceSymbol(title)}*\n\n'
                               f'Артикул: • __{sku}__\n'
                               f'Бренд: • __{brand}__\n\n'
                               f'Цена:\n • {price} ₽  _~{old_price} ₽~_\n\n'
                               f'_«Цена указана без индивидуальной скидки, окончательная '
                               f'сумма зависит от Вашей личной скидки в ЛК WildBerries»_',
                               parse_mode='MarkdownV2')

                bot.send_message(message.chat.id,
                                 'Напишите цену, за которую вы хотели '
                                 'бы купить этот товар _(Только число)_',
                                 reply_markup=keyboard,
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, choose_price)

            else:
                bot.delete_message(message.chat.id, search_message.message_id)
                bot.send_message(message.chat.id,
                                 'Во время проверки ссылки произошла ошибка! Пожалуйста, попробуйте еще раз',
                                 reply_markup=keyboard)
                bot.register_next_step_handler(message, link_request)

        except Exception as e:
            print(e)
            bot.delete_message(message.chat.id, search_message.message_id)
            bot.send_message(message.chat.id, '😵‍💫Упс! Возникла непредвиденная ошибка')


# Запрос желаемой цены
def choose_price(message):
    global selected_price, product_user_id

    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, 'Процесс отменен👍')
    else:
        selected_price = message.text
        selected_price = str(selected_price).replace(',', '.')

        try:
            selected_price = float(selected_price)
            product_user_id = message.from_user.id

            if selected_price == int(selected_price):
                selected_price = int(selected_price)

            if selected_price <= 0:
                bot.send_message(message.chat.id, 'Введите число, большее 0')
                bot.register_next_step_handler(message, choose_price)

            elif float(selected_price) > float(product_price):
                # создаем клавиатуру
                keyboard = types.InlineKeyboardMarkup()

                button1 = types.InlineKeyboardButton(text="Да", callback_data="1")
                button2 = types.InlineKeyboardButton(text="Нет", callback_data="0")
                keyboard.add(button1, button2)

                bot.send_message(message.chat.id, 'Товар стоит девешле той суммы, которую вы ввели. '
                                                  'Хотите ввести другую сумму?', reply_markup=keyboard)
            else:
                msg = add_in_db()
                bot.send_message(message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove())

        except ValueError:
            # создаем клавиатуру
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)

            button = types.KeyboardButton(text="Отмена❌")
            keyboard.add(button)

            bot.send_message(message.chat.id, 'Введите корректное число', reply_markup=keyboard)
            bot.register_next_step_handler(message, choose_price)


# обработка inline клавиатуры
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "1":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id,
                             'Напишите цену, за которую вы хотели '
                             'бы купить этот товар _(Только число)_',
                             parse_mode='Markdown')
            bot.register_next_step_handler(call.message, choose_price)
        elif call.data == "0":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = add_in_db()
            bot.send_message(call.message.chat.id, msg)
        elif call.data == "delete_yes":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "_«Напишите *ПОЛНОЕ* название товара, чтобы удалить его»_",
                             parse_mode='MarkdownV2')
            bot.register_next_step_handler(call.message, delete)
        elif call.data == "cancel":
            bot.delete_message(delete_message.chat.id, delete_message.message_id)
            bot.delete_message(call.message.chat.id, call.message.message_id)


# Добавление товара в Базу Данных
def add_in_db():
    products = sqlite3.connect(PRODUCTS)
    cursor = products.cursor()

    cursor.execute("SELECT user_id, url FROM Products WHERE user_id = ? AND url = ?",
                   (product_user_id, product_url))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO Products (user_id, title, price, selected_price, url) VALUES (?, ?, ?, ?, ?)',
                       (product_user_id, product_title, product_price, selected_price, product_url))
        products.commit()
        products.close()

        users = sqlite3.connect(USERS)
        cursor = users.cursor()

        cursor.execute("SELECT user_id FROM Users WHERE user_id = ?",
                       (product_user_id,))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO Users (user_id) VALUES (?)', (product_user_id,))

        users.commit()
        users.close()
        return '✅Товар добавлен! Я оповещу вас, когда придет время'
    else:
        products.close()
        return 'Я не могу добавить данный товар, потому что вы уже когда-то добавили его'


bot.polling(none_stop=True)
