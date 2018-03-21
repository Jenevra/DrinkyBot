import config
import telebot
import os
import socket
import DBapp
from SPARQLWrapper import SPARQLWrapper, JSON

import json
import io
import requests
import rdflib
import re
from telebot import types

product = "апельсины"

# SPARQL request for getting the category of product


def sparql_request(product):
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

results = sparql_request(product)
for result in results["results"]["bindings"]:
    print(re.search(r'\/(\w*)$', result["type_product"]["value"]).group())
    print("")




# create object bot
bot = telebot.TeleBot(config.token)
x = DBapp.select()
print(x)

@bot.message_handler(content_types=['text'])
def send_message(message):
    bot.send_message(message.chat.id, message.text)



sock = socket.socket()
sock.bind(('', int(os.environ.get('PORT', '5000'))))
sock.listen(1)

if __name__ == '__main__':

    bot.polling(none_stop=True)
