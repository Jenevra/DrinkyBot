import psycopg2

conn = psycopg2.connect("dbname='dcqsh49qsmmirk'"
                        "user='gdwjlbvsahbyvm'"
                        "password='69a4de3f83def198fe16d229ffe0c21c4af205b41307d8fc39d61a18c8b406a9'"
                        "host='ec2-107-21-95-70.compute-1.amazonaws.com'")


def select_user_id(user_id):
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM telegrambot.user_table WHERE user_id=" + str(user_id) + ";")
    records = cur.fetchall()
    return records


def insert_user_table(user_id):
    cur = conn.cursor()
    cur.execute("INSERT INTO telegrambot.user_table(user_id) VALUES(%s)", (user_id,))
    conn.commit()


def select_count_products():
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM telegrambot.product" + ";")
    records = cur.fetchall()
    return records


def insert_product_table(prod_id, name, category):
    cur = conn.cursor()
    cur.execute("INSERT INTO telegrambot.product(product_id, naming, category_id) VALUES(%s, %s, %s)", (prod_id, name, category,))
    conn.commit()


def select_category_from_category_table(name):
    cur = conn.cursor()
    cur.execute("SELECT category_id FROM telegrambot.product WHERE naming=%s", (name,))
    records = cur.fetchall()
    return records


def select_subcategory_from_subcategory_table(name):
    cur = conn.cursor()
    cur.execute("SELECT sub_cat_id FROM telegrambot.drink_subcategory WHERE naming=%s", (name,))
    records = cur.fetchall()
    return records


def select_category_from_subcategory_table(sub_cat):
    cur = conn.cursor()
    cur.execute("SELECT category_drinks FROM telegrambot.drink_subcategory WHERE sub_cat_id=%s", (sub_cat,))
    records = cur.fetchall()
    return records


def select_product_category_from_category_table(name):
    cur = conn.cursor()
    cur.execute("SELECT product_id FROM telegrambot.product WHERE naming=%s", (name,))
    records = cur.fetchall()
    return records


def select_drinks_category_from_drinks_to_drink_table(category):
    cur = conn.cursor()
    cur.execute("SELECT category_drink FROM telegrambot.drinks_to_drink WHERE category_id=%s", (category,))
    records = cur.fetchall()
    return records


def select_drinks_by_categories(category_drinks):
    cur = conn.cursor()
    cur.execute("SELECT sub_cat_id FROM telegrambot.drink_subcategory WHERE category_drinks=%s", (category_drinks,))
    records = cur.fetchall()
    return records


def select_name_drinks_by_subcategories(subcategory):
    cur = conn.cursor()
    cur.execute("SELECT naming FROM telegrambot.drink_subcategory WHERE sub_cat_id=%s", (subcategory,))
    records = cur.fetchall()
    return records


def select_drinks_from_context_table(product):
    cur = conn.cursor()
    cur.execute("SELECT sub_cat_id FROM telegrambot.context_table WHERE product_id=%s", (product,))
    records = cur.fetchall()
    return records


def select_rate_from_global_rate_table(category):
    cur = conn.cursor()
    cur.execute("SELECT rate FROM telegrambot.global_rate WHERE sub_cat_id=%s", (category,))
    records = cur.fetchall()
    return records


def insert_global_rate_none_voted(category):
    cur = conn.cursor()
    cur.execute("INSERT INTO telegrambot.global_rate(sub_cat_id, rate, count_votes) VALUES(%s, %s, %s)", (category, 5, 0))
    conn.commit()


def select_rate_from_user_rate_table(user_id):
    cur = conn.cursor()
    cur.execute("SELECT sub_cat_id, rate FROM telegrambot.user_rate WHERE  user_id=%s", (user_id,))
    records = cur.fetchall()
    return records


def select_data_from_user_rate_table(subcat_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM telegrambot.user_rate WHERE  sub_cat_id=%s", (subcat_id,))
    records = cur.fetchall()
    return records


def insert_into_user_rate(user_id, subcategory, rate):
    cur = conn.cursor()
    cur.execute("INSERT INTO telegrambot.user_rate(user_id, sub_cat_id, rate) VALUES(%s, %s, %s)", (user_id, str(subcategory), rate))
    conn.commit()


def update_global_rate_votes(subcategory):
    cur = conn.cursor()
    cur.execute("UPDATE telegrambot.global_rate SET count_votes = count_votes+%s WHERE sub_cat_id=%s", (1, subcategory))
    conn.commit()


def update_user_rate_votes(new_rate, sub_cat, user_id):
    cur = conn.cursor()
    cur.execute("UPDATE telegrambot.user_rate SET rate = %s WHERE sub_cat_id=%s and user_id=%s", (new_rate, sub_cat, user_id))
    conn.commit()


def insert_into_context_table(user_id, subcategory, product):
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO telegrambot.context_table(user_id, sub_cat_id, product_id) VALUES(%s, %s, %s)", (user_id, str(subcategory), str(product)))
    except psycopg2.IntegrityError:
        pass
    conn.commit()


def select():
    cur = conn.cursor()
    cur.execute("SELECT * FROM telegrambot.user_rate ")
    records = cur.fetchall()
    return records
