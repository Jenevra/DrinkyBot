import config
import telebot
import os
import json
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
dicty = None

sample = None
xc = ["/c_7033", "/с_8174", "/c_1806", "/c_4830", "/c_3131", "/c_785", "/c_2943", "/c_4669", "/ c_6147"]
xcat = ["CAT6", "CAT1", "CAT10", "CAT11", "CAT12", "CAT4", "CAT5", "CAT7", "CAT9"]


def reading_categories():
    global dicty
    dicty = []
    with open('data.json') as data_file:
        data_loaded = json.load(data_file)

    for result in data_loaded["results"]["bindings"]:
        subcat = re.search(r'/(\w*)$', result["subcategory"]["value"]).group()
        cat = re.search(r'/(\w*)$', result["category"]["value"]).group()
        arr = [cat, subcat]
        dicty.append(arr)


def category_return(categ):
    global dicty
    array = []
    for category in categ:
        for x in dicty:
            if x[1] == category:
                array.append(x[0])
    return array


def know_product(categg):
    if categg[0] in xc:
        return categg[0], xc.index(categg[0])
    while True:
        category_array = category_return(categg)
        for x in category_array:
            if x in xc:
                return x, xc.index(x)
        categg = category_array


def formula_of_sample():
    p_parameter = 0.5
    e_parameter = 0.05
    z_parameter = 1.96
    N_parameter = DBapp.select_quantity_users()[0][0]
    print("QUANITY USER ", N_parameter)

    upper_part = (z_parameter ** 2 * p_parameter*(1-p_parameter))/(e_parameter ** 2)
    lower_part = 1 + upper_part / N_parameter

    return upper_part / lower_part


def formula_of_rate(drink):
    global sample
    C_parameter = 6.0

    count_votes = DBapp.select_sum_count_votes()[0][0]
    if count_votes > 500:
        C_parameter = float(DBapp.average_global_score()[0][0])

    R_parameter = float(DBapp.average_rate_of_drink(drink)[0][0])
    v_parameter = float(DBapp.select_count_votes(drink)[0][0])
    m_parameter = float(round(sample, 0))

    upper_part = R_parameter * v_parameter + C_parameter * m_parameter
    lower_part = v_parameter + m_parameter

    return upper_part / lower_part


#score = formula_of_rate("DESVN1")
#print("RATE DRINK = ", score)
#
#DBapp.update_global_rate(score, "DESVN1")


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
    if var_state == config.STATES.S_GLOBAL_BEGIN:
        return "You are in the main menu\n" + \
               "You can start entering /products\n" + \
               "You can see category /statistics\n" + \
               "You can see /drinks_statistic\n" + \
               "Please press one of all command"
    elif var_state == config.STATES.S_CHOOSE_PRODUCT:
        return "You are in process of entering products\n" + \
               "Please continue to ENTER products"
    elif var_state == config.STATES.S_RESET:
        state = config.STATES.S_GLOBAL_BEGIN
        resetted()
        return "I've resetted all of your data, so you can exit or start again"
    elif var_state == config.STATES.S_STATISTIC or var_state == config.STATES.S_DRINKS_STATISTIC:
        return "Continue to choose category"
    elif var_state == config.STATES.S_LOCAL_END:
        state = config.STATES.S_GLOBAL_BEGIN
        return "May be you want to /start again"
    elif var_state == config.STATES.S_CHOOSE_DRINK or var_state == config.STATES.S_OLD_KEYBOARD_STATE:
        return "You are at the point of choosing drink\n" + \
               "Please choose one drink"
    elif var_state == config.STATES.S_KEYBOARD_PRODUCT:
        return "You need to write whatever you want or /reset"
    elif var_state == config.STATES.S_SCORE:
        return "You need to ENTER the score for drink how do you feel about it with your products"


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
    global dicty
    global sample
    state = 0
    sample = 0
    user_id = message.from_user.id
    res_select = DBapp.select_user_id(user_id)
    reading_categories()
    rated = DBapp.select_drinks_global_rated()

    if res_select == []:
        print("there is no such user, so I will add it")
        bot.send_message(message.chat.id, text.start_message_unknown_user)
        DBapp.insert_user_table(user_id)
        print("I added the user")
    else:

        bot.send_message(message.chat.id, text.start_message_known_user)
        print("this user exists")

    quantity_users = DBapp.select_quantity_users()[0][0]
    #quantity_users = 1000
    if quantity_users < 100:
        sample = 20
    elif (quantity_users % 100 == 0 and quantity_users / 100 < 10) or (quantity_users % 1000 == 0 and quantity_users / 100 >= 10):
        sample = formula_of_sample()
        print("NEW SAMPLE IS COUNTED")
        for drink in rated:
            if DBapp.select_count_votes(drink[0])[0][0] > 0:
                global_score = formula_of_rate(drink[0])
                DBapp.update_global_rate(global_score, drink[0])

                print(drink[0])


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, "Hi, my name is Jane Pankratova\n" + \
                                      "I' m the creator of DrinkableBot\n" + \
                                      "If you find mistakes or you aren't agree with bot's choice, \n" +\
                                      "please, make screenshot and contact with me about your problem\n\n" +\
                                      "Email: sunwillshine96@outlook.com\n" + \
                                      "Telegram: genevieve_pn\n" + \
                                      "VK: https://vk.com/pankratova_ev")


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


@bot.message_handler(commands=['statistics'])
def statistic_command(message):
    global state
    naming_drinks_request = DBapp.select_all_categories_of_drink()
    drinks_names = []
    for drink in naming_drinks_request:
        drinks_names.append(drink[0])

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in drinks_names])
    bot.send_message(message.chat.id, 'Choose one category to see statistic', reply_markup=keyboard)
    state = config.STATES.S_STATISTIC


@bot.callback_query_handler(func=lambda c: True and state == config.STATES.S_STATISTIC)
def inlined(c):
    flagg = True
    print("state 8 is here")
    print(c.data)
    clicks = 0.0
    sum_clicks = 0.0
    try:
        clicks = DBapp.select_clicks_for_one(c.data)[0][0]
        sum_clicks = DBapp.select_sum_clicks()[0][0]
    except IndexError:
        flagg = False

    if flagg:
        percentage = clicks / sum_clicks * 100
        answer = ""
        if percentage < 30:
            answer = "It means that less than 30 percent of people choose this category"
        elif 30 <= percentage < 50:
            answer = "The results are average, but " + c.data + " is quite good"
        elif 50 <= percentage < 80:
            answer = "It means that more than half of users choose this category"
        elif percentage >= 80:
            answer = "The most popular drink"

        bot.send_message(c.message.chat.id, "Percentage of choice of drink " + "{:.3f}".format(percentage))
        bot.send_message(c.message.chat.id, answer)
    else:
        bot.send_message(c.message.chat.id, "There is no information about this drink stll")
    bot.send_message(c.message.chat.id, 'Press /continue if you want to continue to look for statistic or /end')


@bot.message_handler(commands=['drinks_statistic'])
def drink_statistic_command(message):
    global state
    naming_drinks_request = DBapp.select_all_categories_of_drink()
    drinks_names = []
    for drink in naming_drinks_request:
        drinks_names.append(drink[0])

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in drinks_names])
    bot.send_message(message.chat.id, 'Choose one category to see drink statistic from this category', reply_markup=keyboard)
    state = config.STATES.S_DRINKS_STATISTIC


@bot.callback_query_handler(func=lambda c: True and state == config.STATES.S_DRINKS_STATISTIC)
def inlinedd(c):
    flagg = True
    print("state 107 is here")
    print(c.data)
    category = DBapp.to_know_category_id_of_drink(c.data)[0][0]
    name_and_rate = DBapp.select_naming_raiting(category)
    if name_and_rate != []:
        for n_r in name_and_rate:
            name = n_r[0]
            rate = n_r[1]

            bot.send_message(c.message.chat.id, "Rate of " + name + " is " + "{:.3f}".format(rate))
        print(name_and_rate)
    else:
        bot.send_message(c.message.chat.id, "There is no information about drinks ib this category stll")
    bot.send_message(c.message.chat.id, 'Press /continue if you want to continue to look for statistic or /end')


@bot.message_handler(commands=['continue'])
def cont(message):
    global state
    print("CONTINUE")
    if state == config.STATES.S_STATISTIC:
        statistic_command(message)
    elif state == config.STATES.S_DRINKS_STATISTIC:
        drink_statistic_command(message)


@bot.message_handler(commands=['end'])
def end(message):
    global state
    state = config.STATES.S_LOCAL_END
    print("END")
    bot.send_message(message.chat.id, check_state(state))


@bot.message_handler(commands=['products'])
def enter_product_handler(message):
    global state
    bot.send_message(message.chat.id, text.choose_product_message)
    state = config.STATES.S_CHOOSE_PRODUCT


@bot.message_handler(func=lambda m: state == config.STATES.S_GLOBAL_BEGIN)
def handler(message):
    global state
    r = message.text
    if r.lower().find("hello") > -1 or r.lower().find("hi") > -1:
        bot.send_message(message.chat.id, text.answer_hello[random.randint(0, 3)])
    elif 'help' in r.split():
        bot.send_message(message.chat.id, text.answer_help)
    elif r.lower().find("bye") > -1 or r.lower().find("goodbye") > -1:
        bot.send_message(message.chat.id, "Goodbye, see you soon")


@bot.message_handler(func=lambda message: state == config.STATES.S_CHOOSE_PRODUCT)
def method(message):
    global state
    global global_drinks
    global global_products_categories
    global drinks_canceled
    global total_product_categories
    catg = []
    total_product_categories = []


    global_products_categories = []
    global_drinks = []
    drinks_chosen = []
    drinks_canceled = []
    print("state = ", message.text)
    parsed_products = re.split('[.,]+', message.text)
    # for each product we look its category (determine what is it)
    for producty in parsed_products:
        category = ""
        product = producty.strip()
        product_category = DBapp.select_category_from_category_table(product)

        print(product_category)
        # if product is in database then we look for for all drinks
        # that are compatible with this product
        if product_category == []:
            results = sparql_request(product)
            for result in results["results"]["bindings"]:
                print(re.search(r'\/(\w*)$', result["type_product"]["value"]).group())
                catg.append(re.search(r'\/(\w*)$', result["type_product"]["value"]).group())
            category_sparql, index = know_product(catg)
            category = xcat[index]
            new_product_id = add_new_product(product, category)
            global_products_categories.append(new_product_id)
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

        print("CANCEL")
        print(cancel)
        bot.send_message(message.chat.id, "I have results, wanna know?")
        state = config.STATES.S_KEYBOARD_PRODUCT


@bot.message_handler(func=lambda message: state == config.STATES.S_KEYBOARD_PRODUCT)
def keyboard1(message):
    global total
    global cancel
    global state
    global old_keyboard_state

    if message.text == "no" or old_keyboard_state == config.STATES.S_OLD_KEYBOARD_STATE:
        print("NO")
        if cancel != []:
            keyboard2 = types.InlineKeyboardMarkup()
            keyboard2.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in cancel])
            bot.send_message(message.chat.id, 'Please score some drinks you have not seen', reply_markup=keyboard2)
            state = config.STATES.S_OLD_KEYBOARD_STATE
        else:
            bot.send_message(message.chat.id, "It was nice to talk with you")
            state = config.STATES.S_RESET
            reset_condition(message)

    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in total])
        bot.send_message(message.chat.id, 'What do you prefer?', reply_markup=keyboard)
        state = config.STATES.S_CHOOSE_DRINK

    print("here 5")


@bot.callback_query_handler(func=lambda c: True and state == config.STATES.S_CHOOSE_DRINK)
def inline1(c):
    bot.send_message(c.message.chat.id, "Enter score for " + c.data)
    global state
    global total

    global nameSubcategory
    nameSubcategory = c.data
    total.remove(c.data)
    print("here")
    print("name =  " + c.data)
    state = config.STATES.S_SCORE

    print("here 1")


@bot.callback_query_handler(func=lambda c: True and state == config.STATES.S_OLD_KEYBOARD_STATE)
def inline2(c):
    bot.send_message(c.message.chat.id, "Enter score for " + c.data)
    global state
    global cancel
    global old_keyboard_state
    global nameSubcategory
    nameSubcategory = c.data
    cancel.remove(c.data)
    print("here")
    print("name =  " + c.data)
    old_keyboard_state = config.STATES.S_OLD_KEYBOARD_STATE
    state = config.STATES.S_SCORE

    print("here 10")


@bot.message_handler(func=lambda message:  state == config.STATES.S_SCORE)
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
        state = config.STATES.S_KEYBOARD_PRODUCT
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
            DBapp.update_global_rate_votes(subcategory_drink)

            print("inserted")
        else:
            DBapp.update_user_rate_votes(scoreProd, subcategory_drink, user_id)

            print("updated")

        rate = formula_of_rate(subcategory_drink)
        DBapp.update_global_rate(rate, subcategory_drink)

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

