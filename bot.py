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
    """This method reads categories from JSON file
    and add them to global parameter dicty
    for non-reading and non-looking forward to category
    every time when there is no product in database

    """
    global dicty
    dicty = []
    with open('data.json') as data_file:
        data_loaded = json.load(data_file)

    for result in data_loaded["results"]["bindings"]:
        subcat = re.search(r'/(\w*)$', result["subcategory"]["value"]).group()
        cat = re.search(r'/(\w*)$', result["category"]["value"]).group()
        arr = [cat, subcat]
        dicty.append(arr)


def category_return(subcat):
    """This method is looking for category of subcategory
    If sub is equal to x[1], we add to array category (x[0]) of subcategory (x[1] == sub)

    :param subcat: subcategory which is being searched for
    :return: array of categories
    """
    global dicty
    array = []
    for sub in subcat:
        for x in dicty:
            if x[1] == sub:
                array.append(x[0])
    return array


def know_product(categg):
    """This method is looking for index of AGROVOC category
    and with the help of this index we will find Database category,
    because two global arrays are identical to each other
    (on the same positions are the same categories with different ids)

    :param categg: AGROVOC category
    :return: category id, index in global array of  AGROVOC categories
    """
    if categg[0] in xc:
        return categg[0], xc.index(categg[0])
    while True:
        category_array = category_return(categg)
        for x in category_array:
            if x in xc:
                return x, xc.index(x)
        categg = category_array


def formula_of_sample():
    """This method is calculating the sample size
    for the formula 2.2

    :return: sample size
    """
    p_parameter = 0.5
    e_parameter = 0.05
    z_parameter = 1.96
    N_parameter = DBapp.select_quantity_users()[0][0]

    upper_part = (z_parameter ** 2 * p_parameter*(1-p_parameter))/(e_parameter ** 2)
    lower_part = 1 + upper_part / N_parameter

    return upper_part / lower_part


def formula_of_rate(drink):
    """This method is calculating the rate of the specific drink
    with the help of formula 2.1

    Here there is a check whether enough votes to recalculate the average
    (C_parameter) or not

    :param drink: drink for which is considered a rating
    :return: rate of drink
    """
    global sample
    C_parameter = 6.0

    count_votes = DBapp.select_sum_count_votes(drink)[0][0]
    if count_votes > 500:
        C_parameter = float(DBapp.average_global_score()[0][0])

    R_parameter = float(DBapp.average_rate_of_drink(drink)[0][0])
    v_parameter = float(DBapp.select_count_votes(drink)[0][0])
    m_parameter = float(round(sample, 0))

    upper_part = R_parameter * v_parameter + C_parameter * m_parameter
    lower_part = v_parameter + m_parameter

    return upper_part / lower_part


def sparql_request(product):
    """Make a request to SPARQL access point to get the category of product
    if it is not known (there is no such entry in Database)

    :param product: the naming of entered by user product
    :return: AGROVOC category
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
    """This method is adding new product to database

    :param product_name: name of new product
    :param product_category: category of product
    :return: new id of product
    """
    records = DBapp.select_count_products()
    number_product = records[0][0] + 1
    print(number_product)

    new_product_name = "PROD" + str(number_product)
    DBapp.insert_product_table(new_product_name, product_name, product_category)
    print("x")
    return new_product_name


def check_state(var_state):
    """This method is checking the state in which bot is working now
    and send message for current situation

    :param var_state: state of program
    :return: message
    """
    global state
    if var_state == config.STATES.S_GLOBAL_BEGIN:
        return "Ты в главном меню\n" + \
               "Можешь начать вводить продукты /products\n" + \
               "Можешь посмотреть статистику категорий напитков /statistics\n" + \
               "Можешь посмотреть статистику по отдельным напиткам /drinks_statistic\n" + \
               "Нажми одну из команд"
    elif var_state == config.STATES.S_CHOOSE_PRODUCT:
        return "You are in process of entering products\n" + \
               "Please continue to ENTER products"
    elif var_state == config.STATES.S_RESET:
        state = config.STATES.S_GLOBAL_BEGIN
        resetted()
        return "Можешь начать снова в любой момент"
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
    """This method resets all the data when user calls the command /reset

    :return: nothing
    """
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
    """Handler for command /start
    Here is a check whether user is new or not
    Also some pre-start steps are finished:
        1. Size of sample is calculating
        2. If user is every 100 person or 1000 then global rates are recalculating
        3. And here there is a reading categories once time in use

    :param message:
    :return:
    """
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

        print("I added the user")
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
    """Handler for command /info
    Information for feedback

    :param message:
    :return:
    """
    bot.send_message(message.chat.id, "Привет, меня зовут Панкратова Евгения\n" + \
                                      "Я разработчик этого прекрасного бота DrinkableBot\n" + \
                                      "Если ты нашел ошибку или не согласен с выбором бота, \n" +\
                                      "пожалуйста,сделай скриншот и расскажи мне о своей проблеме\n\n" +\
                                      "Email: sunwillshine96@outlook.com\n" + \
                                      "Telegram: genevieve_pn\n" + \
                                      "VK: https://vk.com/pankratova_ev")


@bot.message_handler(commands=['help'])
def help_with_advice(message):
    """Handler for command /help
    Send help information

    :param message:
    :return:
    """
    global state
    bot.send_message(message.chat.id, text.help_message)
    bot.send_message(message.chat.id, check_state(state))


@bot.message_handler(commands=['reset'])
def reset_condition(message):
    """Handler for command /reset
    Resetting all the data

    :param message:
    :return:
    """
    global state
    bot.send_message(message.chat.id, text.reset_message)
    state = config.STATES.S_RESET
    bot.send_message(message.chat.id, check_state(state))


@bot.message_handler(commands=['statistics'])
def statistic_command(message):
    """Handler for command /statistics
    Send the keyboard to user to choose one of the categories to see
    statistic

    :param message:
    :return:
    """
    global state
    naming_drinks_request = DBapp.select_all_categories_of_drink()
    drinks_names = []
    for drink in naming_drinks_request:
        drinks_names.append(drink[0])

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in drinks_names])
    bot.send_message(message.chat.id, 'Выбери одну из категорий, чтобы посмотреть статистику', reply_markup=keyboard)
    state = config.STATES.S_STATISTIC


@bot.callback_query_handler(func=lambda c: True and state == config.STATES.S_STATISTIC)
def inlined(c):
    """Handler for keyboard of def statictic_command(...)

    :param c: chosen category
    :return:
    """
    flagg = True
    print("state 8 is here")
    print(c.data)
    clicks = 0.0
    sum_clicks = 0.0
    try:
        clicks = DBapp.select_clicks_for_one(c.data)[0][0]
        sum_clicks = DBapp.select_sum_clicks()[0][0]

        cat_id = DBapp.to_know_category_id_of_drink(c.data)[0][0]
        sum_votes = DBapp.select_sum_count_votes(cat_id)[0][0]
        positive_votes = DBapp.select_sum_positive_votes(cat_id)[0][0]
        print("SUM VOTES FOR CHOSEN CATEGORY = ", sum_votes)
        print("POSITIVE VOTES FOR CHOSEN CATEGORY = ", positive_votes)
    except IndexError:
        flagg = False

    if flagg:
        percentage = positive_votes / sum_votes * 100
        answer = ""
        if percentage < 40:
            answer = "Процент положительных оценок здесь очень мал к сожалению."
        elif 40 <= percentage < 50:
            answer = "Результаты конечно средние, но данная категория ' " + c.data + " ' достаточно хороша."
        elif 50 <= percentage < 80:
            answer = "Больше половины положительно оцененных напитков приходится на эту категорию. Бери не прогадаешь."
        elif percentage >= 80:
            answer = "Это лучшее что можно придумать"

        bot.send_message(c.message.chat.id, "Переходов, совершенных по данной категории: " + str(clicks) + " из " + str(sum_clicks))
        bot.send_message(c.message.chat.id, "Процент положительных оценок напитков из категории (оценка 5-10): " + " {:.2f}".format(percentage))
        bot.send_message(c.message.chat.id, answer)
    else:
        bot.send_message(c.message.chat.id, "К сожалению, напитков этой категории еще не выбирали.")
    bot.send_message(c.message.chat.id, 'Нажми /continue если хочешь продолжить смотреть статистику или чтобы закончить /end')


@bot.message_handler(commands=['drinks_statistic'])
def drink_statistic_command(message):
    """Handler for command /drinks_statistic
    Send the keyboard to user to choose one of the categories to see
    statistic

    :param message:
    :return:
    """
    global state
    naming_drinks_request = DBapp.select_all_categories_of_drink()
    drinks_names = []
    for drink in naming_drinks_request:
        drinks_names.append(drink[0])

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in drinks_names])
    bot.send_message(message.chat.id, 'Выбери одну из категорий, чтобы увидеть статистику по напиткам', reply_markup=keyboard)
    state = config.STATES.S_DRINKS_STATISTIC


@bot.callback_query_handler(func=lambda c: True and state == config.STATES.S_DRINKS_STATISTIC)
def inlinedd(c):
    """Handler for keyboard of def drink_statictic_command(...)
    Send user rate of drinks from the chosen category

    :param c: chosen category
    :return:
    """
    print(c.data)
    category = DBapp.to_know_category_id_of_drink(c.data)[0][0]
    name_and_rate = DBapp.select_naming_raiting(category)
    if name_and_rate != []:
        for n_r in name_and_rate:
            name = n_r[0]
            rate = n_r[1]

            bot.send_message(c.message.chat.id, "Рейтинг напитка " + name + ": " + "{:.3f}".format(rate))
        print(name_and_rate)
    else:
        bot.send_message(c.message.chat.id, "Еще нет информации по данной категории")
    bot.send_message(c.message.chat.id, 'Нажми /continue если хочешь продолжить смотреть статистику или чтобы закончить /end')


@bot.message_handler(commands=['continue'])
def cont(message):
    """Handler for command /continue
    Local handler for statistic commands
    Is checking which message is to be send to user

    :param message:
    :return:
    """
    global state
    print("CONTINUE")
    if state == config.STATES.S_STATISTIC:
        statistic_command(message)
    elif state == config.STATES.S_DRINKS_STATISTIC:
        drink_statistic_command(message)


@bot.message_handler(commands=['end'])
def end(message):
    """Handler for command /continue
    Local handler for statistic commands

    :param message:
    :return:
    """
    global state
    state = config.STATES.S_LOCAL_END
    print("END")
    bot.send_message(message.chat.id, check_state(state))


@bot.message_handler(commands=['products'])
def enter_product_handler(message):
    """Handler for command /products
    Send messages and goes to another method which is doing algoritm of analyzing
    products and choosing drinks

    :param message:
    :return:
    """
    global state
    print("MESSAGE FROM ", message.from_user.id)
    bot.send_message(message.chat.id, text.choose_product_message)
    state = config.STATES.S_CHOOSE_PRODUCT


@bot.message_handler(func=lambda m: state == config.STATES.S_GLOBAL_BEGIN)
def handler(message):
    global state
    r = message.text
    if "привет" in r.lower.split() or "hi" in r.lower.split():
        bot.send_message(message.chat.id, text.answer_hello[random.randint(0, 3)])
    elif 'помоги' in r.split():
        bot.send_message(message.chat.id, text.answer_help)
    elif "пока" in r.lower.split() or "goodbye" in r.lower.split():
        bot.send_message(message.chat.id, "Пока, возвращайся скорее")


@bot.message_handler(func=lambda message: state == config.STATES.S_CHOOSE_PRODUCT)
def method(message):
    """This method performs the developed algorithm of choosing drinks
    First we are analyzing products which were entered by user,
    we are looking for them in database and add their categories to global_products_categories
    If there are no such entry, we make request to AGROVOC database.
    Then just adding drinks from DB which are compatible with such category.

    Check if global_drinks is empty, it means program could find nothing, and it send special message.
    If not, this first selected set is going through stages of the algoritm
    After results are got, we go to another state of program (another handler)

    :param message:
    :return:
    """
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
        bot.send_message(message.chat.id, "Хочу тебе кое-что предложить, не против?")
        state = config.STATES.S_KEYBOARD_PRODUCT


@bot.message_handler(func=lambda message: state == config.STATES.S_KEYBOARD_PRODUCT)
def keyboard1(message):
    """Handler which send user keyboard with result drinks
    and offer user to choose drinks

    If there are cancelled drinks (drinks which are not appropriate for entered products)
    after basic choose step, user is offered to score these drinks just for scaling the global rate table
    and to indicate which drinks he likes (scored with 5-10) or does not (scored 1-4)

    :param message:
    :return:
    """
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
            bot.send_message(message.chat.id, "Было интересно с тобой пообщаться")
            state = config.STATES.S_RESET
            reset_condition(message)

    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=name) for name in total])
        bot.send_message(message.chat.id, 'Выбери что-нибудь', reply_markup=keyboard)
        state = config.STATES.S_CHOOSE_DRINK

    print("here 5")


@bot.callback_query_handler(func=lambda c: True and state == config.STATES.S_CHOOSE_DRINK)
def inline1(c):
    """Handler for offering to score appropriate drink

    :param c: chosen drink
    :return:
    """
    bot.send_message(c.message.chat.id, "Хороший выбор, оцени его (1-10): " + c.data)
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
    """Handler for offering to score cancelled drinks

    :param c: chosen drink
    :return:
    """
    bot.send_message(c.message.chat.id, "Хороший выбор, оцени его (1-10): " + c.data)
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
    """This method insert/update local user score for chosen drink
    Also it is re-calculating rate of this drink and add this rate to global rate table
    Checking if user enter the score not the set of symbols

    :param message:
    :return:
    """
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
            bot.send_message(message.chat.id, "Если хочешь выбирать дальше, набери ДА, если нет можешь выйти /reset")
        else:
            for x in global_products_categories:
                DBapp.insert_into_context_table(user_id, subcategory_drink, x)
            bot.send_message(message.chat.id, "Если хочешь выбирать дальше, набери ДА, если нет можешь выйти /reset")

    else:
        bot.send_message(message.chat.id, "Ты ввел что-то не то, попробуй еще раз!")

    print("here 2")


DRINKS = None


def simple_drinks_handler(drinks_to_choose, drinks_to_cancel):
    """Zero step of selection of drinks - simple selection

    :param drinks_to_choose:
    :param drinks_to_cancel:
    :return:
    """
    global global_drinks
    subcategories = {}
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
    """First step of selection of drinks - context based

    :param chosen:
    :param canceled:
    :return:
    """
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


def global_rate_handler(chosen):
    """Second step of selection of drinks - based on global rate

    :param chosen:
    :return:
    """
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


def user_rate_handler(chosen):
    """Third step of selection of drinks - based on own user rate

    :param chosen:
    :return:
    """
    global user_id
    user_rate = DBapp.select_rate_from_user_rate_table(user_id)
    print("USER RATED ", user_rate)
    for x in user_rate:
        if x[0] in chosen and x[1] < 5:
            chosen.remove(x[0])
            print("SHOULD BE REMOVE", chosen)
            print(x[0])
        print(x[1])
    print(user_rate)
    print("WHY ", chosen)


sock = socket.socket()
sock.bind(('', int(os.environ.get('PORT', '5000'))))
sock.listen(1)
bot.polling()

