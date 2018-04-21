import psycopg2
import config
import telebot
import os
import socket
import DBapp
import text
import random
from SPARQLWrapper import SPARQLWrapper, JSON
import re
from statistics import median
from telebot import types


old_keyboard_state = None
user_id = None
state = 0
total_product_id = None

proc = 0.5

total = None
cancel = None

flag = False

nameSubcategory = None
scoreProd = None

drinks_canceled = None
global_drinks = None
global_products_categories = None


def sparql_request(product):
    """Make a request to SPARQL access point to get the category of product
    if it is not known (there is no such entry in Database)

    Keyword arguments:
        product -- the naming of entered by user product
    """
    sparql = SPARQLWrapper(config.http)
    requests = """

        PREFIX skos:	<http://www.w3.org/2004/02/skos/core#>
        SELECT ?prod_code  ?name  ?type_product ?type_naming
        WHERE
        {
            ?prod_code  skos:prefLabel ?name.
            ?prod_code skos:broader ?type_product.
            ?type_product skos:prefLabel ?type_naming.

            FILTER ( str(?name)= """ + '\"' + product\
               + '\"' + """ )
        }
        LIMIT 1
        """

    print(requests)
    sparql.setQuery(requests)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


# create object bot
bot = telebot.TeleBot(config.token)


# method for adding new product if it is does not exist in database
def add_new_product(product_name, product_category):
    records = DBapp.select_count_products()
    number_product = records[0][0] + 1
    print(number_product)

    new_product_name = "PROD" + str(number_product)
    DBapp.insert_product_table(new_product_name, product_name, product_category)
    print("x")
    return new_product_name


#add_new_product("улитки", "CAT6")

def check_state(var_state):
    global state
    if var_state == 0:
        return "Please press one of all command"
    elif var_state == 1:
        return "Please continue to ENTER products"
    elif var_state == 8:
        state = 0
        resetted()
        return "I've resetted all of your data, so you can exit or start again"


def resetted():
    global total
    global cancel
    global old_keyboard_state
    global nameSubcategory
    global scoreProd
    global drinks_canceled
    global global_drinks
    global global_products_categories

    total = None
    cancel = None
    old_keyboard_state = None
    nameSubcategory = None
    scoreProd = None
    drinks_canceled = None
    global_drinks = None
    global_products_categories = None


@bot.message_handler(commands=['start'])
def start(message):
    global user_id
    global state
    user_id = message.from_user.id
    res_select = DBapp.select_user_id(user_id)
    if res_select == []:
        print("there is no such user, so I will add it")
        bot.send_message(message.chat.id, text.start_message_unknown_user)
        DBapp.insert_user_table(user_id)
        print("I added the user")
    else:

        bot.send_message(message.chat.id, text.start_message_known_user)
        print("this user exists")


@bot.message_handler(commands=['help'])
def help_with_advice(message):
    global state
    bot.send_message(message.chat.id, text.help_message)
    bot.send_message(message.chat.id, check_state(state))


@bot.message_handler(commands=['reset'])
def reset_condition(message):
    global state
    bot.send_message(message.chat.id, text.reset_message)
    state = config.STATES.S_RESET
    bot.send_message(message.chat.id, check_state(state))


@bot.message_handler(commands=['products'])
def enter_product_handler(message):
    global state
    bot.send_message(message.chat.id, text.choose_product_message)
    state = config.STATES.S_CHOOSE_PRODUCT


@bot.message_handler(func=lambda m: state == 0)
def handler(message):
    global state
    r = message.text
    if r.lower() in ['hello', 'hi']:
        bot.send_message(message.chat.id, text.answer_hello[random.randint(0, 3)])
    elif 'help' in r.split():
        bot.send_message(message.chat.id, text.answer_help)


@bot.message_handler(func=lambda message: state == config.STATES.S_CHOOSE_PRODUCT)
def method(message):
    global state
    global global_drinks
    global global_products_categories
    global drinks_canceled
    global total_product_categories
    total_product_categories = []

    global_products_categories = []
    global_drinks = []
    drinks_chosen = []
    drinks_canceled = []
    print("state = ", message.text)
    parsed_products = re.split('[., ]+', message.text)
    # for each product we look its category (determine what is it)
    for product in parsed_products:
        product_category = DBapp.select_category_from_category_table(product)

        print(product_category)
        # if product is in database then we look for for all drinks
        # that are compatible with this product
        if product_category == []:
            category = "AAA"
            #results = sparql_request(product)
            #for result in results["results"]["bindings"]:
            #    print(re.search(r'\/(\w*)$', result["type_product"]["value"]).group())
            #    # получить здесь человеческую категорию продукта (преобразование категорий)
            #    # category = ...
            # добавить категорию чтоб она добавляалсь в global_products_categories
        else:
            global_products_categories.append(DBapp.select_product_category_from_category_table(product)[0][0])
            category = product_category[0][0]

        drinks_category = DBapp.select_drinks_category_from_drinks_to_drink_table(category)

        for drink in drinks_category:
            global_drinks.append(drink[0])

    if global_drinks == []:
        bot.send_message(message.chat.id, text.nothing_to_find[random.randint(0, 2)])
        state = 0
    else:
        simple_drinks_handler(drinks_chosen, drinks_canceled)
        context_drinks_handler(drinks_chosen, drinks_canceled)
        drinks_chosen = global_rate_handler(drinks_chosen)

        user_rate_handler(drinks_chosen)
        print("drinks after global and user rate ", drinks_chosen)
        print(total_product_categories)
        global total
        total = []

        for x in drinks_chosen:
            total.append(DBapp.select_name_drinks_by_subcategories(x)[0][0])

        global cancel
        cancel = []

        for x in drinks_canceled:
            cancel.append(DBapp.select_name_drinks_by_subcategories(x)[0][0])

        bot.send_message(message.chat.id, "I have results, wanna know?")
        state = 200


@bot.message_handler(func=lambda message: state == 200)
def keyboard1(message):
    global total
    global cancel
    global state
    global old_keyboard_state

    if message.text == "no" or old_keyboard_state == 150:
        print("NO")
        if cancel != []:
            keyboard2 = types.InlineKeyboardMarkup()
            keyboard2.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in cancel])
            bot.send_message(message.chat.id, 'Please score some drinks you have not seen', reply_markup=keyboard2)
            state = 150
        else:
            bot.send_message(message.chat.id, "It was nice to talk with you")
            state = 8
            reset_condition(message)

    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in total])
        bot.send_message(message.chat.id, 'What do you prefer?', reply_markup=keyboard)
        state = 15

    print("here 5")


@bot.callback_query_handler(func=lambda c: True and state == 15)
def inline(c):
    bot.send_message(c.message.chat.id, "Enter score for " + c.data)
    global state
    global total

    global nameSubcategory
    nameSubcategory = c.data

    total.remove(c.data)
    print("here")
    print("name =  " + c.data)
    state = 122

    print("here 1")


@bot.callback_query_handler(func=lambda c: True and state == 150)
def inline(c):
    bot.send_message(c.message.chat.id, "Enter score for " + c.data)
    global state
    global cancel
    global old_keyboard_state
    global nameSubcategory
    nameSubcategory = c.data

    cancel.remove(c.data)
    print("here")
    print("name =  " + c.data)
    old_keyboard_state = 150
    state = 122

    print("here 10")


@bot.message_handler(func=lambda message:  state == 122)
def score(message):
    global state
    global nameSubcategory
    global scoreProd
    global user_id
    global old_keyboard_state
    global global_products_categories
    scoreProd = message.text
    flag = True
    print(state)
    if message.text.isdecimal():
        state = 200
        print("name =  " + nameSubcategory)
        print("score = " + message.text)
        select_result = DBapp.select_category_and_subcategory_from_subcategory_table(nameSubcategory)
        subcategory_drink = select_result[0][1]
        category_drink = select_result[0][0]

        print("check category ", category_drink)
        print(subcategory_drink)

        if DBapp.select_for_checking_existing(category_drink) == []:
            DBapp.insert_into_category_rate(category_drink)
        else:
            DBapp.update_category_rate_clicks(category_drink)

        if DBapp.select_data_from_user_rate_table(subcategory_drink) == []:
            DBapp.insert_into_user_rate(user_id, subcategory_drink, scoreProd)
            flag = True
            print("inserted")
        else:
            DBapp.update_user_rate_votes(scoreProd, subcategory_drink, user_id)
            flag = False
            print("updated")

        if flag:
            DBapp.update_global_rate_votes(subcategory_drink)
        else:
            pass

        if old_keyboard_state:
            bot.send_message(message.chat.id, "If you wanna continue type something or command reset")
        else:
            for x in global_products_categories:
                DBapp.insert_into_context_table(user_id, subcategory_drink, x)

            bot.send_message(message.chat.id, "If you wanna continue type something if not type NO or command reset")

    else:
        bot.send_message(message.chat.id, "You didn't enter the right score")

    print("here 2")


DRINKS = None


# 0ой этап отбора
def simple_drinks_handler(drinks_to_choose, drinks_to_cancel):
    global global_drinks
    subcategories = {}
    # получаем частотный словарь по напиткам
    for drink in global_drinks:
        sub = DBapp.select_drinks_by_categories(drink)
        for x in sub:
            if subcategories.__contains__(x[0]):
                subcategories[x[0]] += 1
            else:
                subcategories.update({x[0]: 1})

    maxi = max(subcategories.values())

    for x in subcategories:
        if subcategories[x] / maxi > proc:
            drinks_to_choose.append(x)
        else:
            drinks_to_cancel.append(x)
    print(drinks_to_choose)
    print(drinks_to_cancel)


# 1ый этап - контекст
def context_drinks_handler(chosen, canceled):
    global global_products_categories
    for cat in global_products_categories:
        print("product_id = " + cat)
        for drink in DBapp.select_drinks_from_context_table(cat):
            if drink[0] in canceled:
                pass
            elif drink[0] in chosen:
                pass
            else:
                chosen.append(drink[0])


# 2ой этап - выбор по глобальным оценкам
def global_rate_handler(chosen):
    global_rate_drinks = {}
    for drink in chosen:
        rate = DBapp.select_rate_from_global_rate_table(drink)
        if rate == []:
            DBapp.insert_global_rate_none_voted(drink)
            global_rate_drinks.update({drink: 5.0})
            print("x")
        else:
            global_rate_drinks.update({drink: float(rate[0][0])})
    mediana = median(global_rate_drinks.values())

    drinks_after_rate = []
    for x in global_rate_drinks:
        if global_rate_drinks[x] >= mediana:
            drinks_after_rate.append(x)

    return drinks_after_rate


# 3 этап - выбор по оценкам пользователя
def user_rate_handler(chosen):
    global user_id
    user_rate = DBapp.select_rate_from_user_rate_table(user_id)
    for x in user_rate:
        if x[0] in chosen and x[1] < 5:
            chosen.remove(x[0])
        print(x[0])
        print(x[1])
    print(user_rate)


sock = socket.socket()
sock.bind(('', int(os.environ.get('PORT', '5000'))))
sock.listen(1)
bot.polling()

