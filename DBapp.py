import psycopg2

conn = psycopg2.connect("dbname='dcqsh49qsmmirk'"
                        "user='gdwjlbvsahbyvm'"
                        "password='69a4de3f83def198fe16d229ffe0c21c4af205b41307d8fc39d61a18c8b406a9'"
                        "host='ec2-107-21-95-70.compute-1.amazonaws.com'")


def select():
    cur = conn.cursor()
    cur.execute("select category_id from telegrambot.product_category")
    records = cur.fetchall()
    return records