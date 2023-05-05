import random
import time
import os
import sys
import pymongo
import json
from pymongo import MongoClient
import pandas as pd
import numpy as np
import requests
import ast
from datetime import datetime
from json.decoder import JSONDecodeError
from typing import List, Dict, Any
import yaml
from bson import json_util


sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
from gpt4free import you, forefront, quora, usesless, theb, italygpt
import re

CLEANR = re.compile('<.*?>')
italygpt = italygpt.Completion()

# initialize api
italygpt.init()

API_URL = 'https://orc.kapinsights.com/request_documents'


def cleanhtml(raw_html):
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext


def get_answer_italy(question: str) -> str:
    # Set cloudflare clearance cookie and get answer from GPT-4 model
    try:
        # get an answer
        italygpt.create(prompt=question)
        result = cleanhtml(italygpt.answer)
        return result

    except Exception as e:
        # Return error message if an exception occurs
        return (
            f'An error occurred: {e}. Please make sure you are using a valid cloudflare clearance token and user agent.'
        )

def get_answer_you(question: str) -> str:
    # Set cloudflare clearance cookie and get answer from GPT-4 model
    try:
        result = you.Completion.create(prompt=question)

        return result.text

    except Exception as e:
        # Return error message if an exception occurs
        return (
            f'An error occurred: {e}. Please make sure you are using a valid cloudflare clearance token and user agent.'
        )


def get_answer_forefront(question: str) -> str:
    # Set cloudflare clearance cookie and get answer from GPT-4 model
    try:
        # create an account
        token = forefront.Account.create(logging=False)
        print(token)
        result = forefront.Completion.create(prompt=question, token=token)
        return result.text

    except Exception as e:
        # Return error message if an exception occurs
        return (
            f'An error occurred: {e}. Please make sure you are using a valid cloudflare clearance token and user agent.'
        )


def get_answer_quora(question: str) -> str:
    # Set cloudflare clearance cookie and get answer from GPT-4 model
    try:
        result = quora.Completion.create(prompt=question, model='ChatGPT', token="fHkW8210dBzpKD2j2AgN3w%3D%3D")

        return result.text

    except Exception as e:
        # Return error message if an exception occurs
        return (
            f'An error occurred: {e}. Please make sure you are using a valid cloudflare clearance token and user agent.'
        )


def get_answer_usesless(question: str) -> str:
    # Set cloudflare clearance cookie and get answer from GPT-4 model
    try:
        result = usesless.Completion.create(prompt=question)

        return result['text']

    except Exception as e:
        # Return error message if an exception occurs
        return (
            f'An error occurred: {e}. Please make sure you are using a valid cloudflare clearance token and user agent.'
        )


def get_answer_theb(question: str) -> str:
    # Set cloudflare clearance cookie and get answer from GPT-4 model
    try:
        result = ""
        for token in theb.Completion.create(prompt=question):
            result = result + token
        return result

    except Exception as e:
        # Return error message if an exception occurs
        return (
            f'An error occurred: {e}. Please make sure you are using a valid cloudflare clearance token and user agent.'
        )


class NoAnswerFoundError(Exception):
    pass


def get_answer(question: str):
    functions = [get_answer_you, get_answer_quora, get_answer_usesless, get_answer_theb]
    random.shuffle(functions)

    for function in functions:
        for i in range(5):
            try:
                answer = function(question)
                print("answer:", answer, "by function:", function)
                first_two = answer[:2]
                is_economic = update_es_economica_gpt(first_two)
                if is_economic != "Unknown":
                    return answer, is_economic, str(function)
            except:
                pass
            time.sleep(1)

    raise NoAnswerFoundError("Sorry, I could not find an answer.")


# Update the es_economica_gpt column based on the conditions
def update_es_economica_gpt(value):
    if "no" in value.lower():
        return "No"
    elif "sí" in value.lower() or "si" in value.lower():
        return "Sí"
    else:
        return "Unknown"


# Function to ask GPT-3 if the article is an economic article or not
def is_economic_article(document, collection):
    article = document['Desc_Noticia']
    article_id = document['_id']['$oid']
    document['_id'] = article_id
    try:
        prompt = f"Clasifica el siguiente artículo de noticias en si es o no una noticia económica, responder exclusivamente Sí o No. articulo: {article}"
        full_answer, short_answere, service = get_answer(prompt)
        # Update the document in the collection
        document['es_economica_gpt'] = short_answere
        document['gpt_completa'] = full_answer
        update_all(collection, document)
        current_time = datetime.now()
        print(str(current_time), "articulo:", article_id, "es:", short_answere, "y fue actualizado en la base de datos. respuesta de GTP:",
              full_answer, "servicio:", service)
    except Exception as e:
        print(f"An exception occurred while processing article_id {article_id}: {e}")


def read_all_document(collection):
    return collection.find()


# Update all
def update_all(coleccion, document):
    coleccion.replace_one({"_id": document["_id"]}, document)


# Define the worker function for concurrent execution
def worker(documents, collection):
    for document in documents:
        is_economic_article(document, collection)

def request_docs():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        response_content_str = response.content.decode('utf-8')
        json_data = json.loads(response_content_str)
        json_data = json.loads(json_data)
        return json_data
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing response from API: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"Error accessing API: {e}")



# Connect to MongoDB
client = MongoClient(
    "mongodb://inst-newstic:7E69wh96tzcKjK5u3tnFHK7BwbpT2dbU61JsXxVsYdPNTuazAGNBZQPxNo6xaQcDJbxlsIKmiDrhACDbDy1fmg%3D%3D@inst-newstic.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@inst-newstic@")
db = client["newstic"]
collection = db["TIE_Modelo_Economia"]

documents_for_similarity_calc = request_docs()
print("# de Documentos a procesar:", len(documents_for_similarity_calc))

# Loop while both queries return non-empty results
while len(documents_for_similarity_calc) > 0:
    # Limpieza Noticias
    worker(documents=documents_for_similarity_calc, collection=collection)
    documents_for_similarity_calc = request_docs()
    print("# de Documentos a procesar:", len(documents_for_similarity_calc))
