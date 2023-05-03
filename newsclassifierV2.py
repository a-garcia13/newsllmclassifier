import random
import time
import os
import sys
import pymongo
from pymongo import MongoClient
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
from gpt4free import you, forefront, quora, usesless, theb


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
        result = forefront.Completion.create(prompt=question,
                                             token='eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yTzZ3UTFYd3dxVFdXUWUyQ1VYZHZ2bnNaY2UiLCJ0eXAiOiJKV1QifQ.eyJhenAiOiJodHRwczovL2NoYXQuZm9yZWZyb250LmFpIiwiZXhwIjoxNjgyOTQ5MTE2LCJpYXQiOjE2ODI5NDkwNTYsImlzcyI6Imh0dHBzOi8vY2xlcmsuZm9yZWZyb250LmFpIiwibmJmIjoxNjgyOTQ5MDQ2LCJzaWQiOiJzZXNzXzJQOVFvSWlGSzNkeFVoUVJXRkVSR0hxa2FXTiIsInN1YiI6InVzZXJfMlA5UW9FU1Q1SGlUSjhXQVFVZjRZVUprRGM5In0.fTuZZj4LhjY62Z1P-nsfKUzeMik-msSnHbyqA4VqDf6hykZlW-nCY1bsDUJ1KPTGy5KaM8DTdi1KxiySReZzUtF_I8s32_UJYtMu7tu7A_Y-N57kypb8XZm54gUrOa0qoMcqxSBrkv6nbWBXQomo21l_Qrpxp6NVe-CwPFx9AJ1k8XCrCc2BkfxF8O_OdZg22b9KqLushQEtW0J2Ys4bB7ZajQIaMfo2tfa1Tng-M7sk7OO2zPdlibRhl7960cwOG8EGq1f2P0tjXhHyuAeIr2gIBfQXK3hrM6VPA1-wN7CrBN3OXF91LXLr1-dnqNZFRghFjsmv35WjNvW5bP-CQQ')

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
    functions = [get_answer_you, get_answer_forefront, get_answer_quora, get_answer_usesless, get_answer_theb]
    random.shuffle(functions)

    for function in functions:
        for i in range(5):
            try:
                answer = function(question)
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
    article_id = document['_id']
    try:
        prompt = f"Clasifica el siguiente artículo de noticias en si es o no una noticia económica, responder exclusivamente Sí o No. articulo: {article}"
        full_answer, short_answere, service = get_answer(prompt)
        # Update the document in the collection
        document['es_economica_gpt'] = short_answere
        document['gpt_completa'] = full_answer
        update_all(collection, document)
        current_time = datetime.now()
        print(str(current_time), "articulo:", article_id, "es:", short_answere,
              "y fue actualizado en la base de datos. respuesta de GTP:",
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


# Connect to MongoDB
client = MongoClient(
    "mongodb://inst-newstic:7E69wh96tzcKjK5u3tnFHK7BwbpT2dbU61JsXxVsYdPNTuazAGNBZQPxNo6xaQcDJbxlsIKmiDrhACDbDy1fmg%3D%3D@inst-newstic.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@inst-newstic@")
db = client["newstic"]
collection = db["TIE_Modelo_Economia"]

query_limp = {
    "Desc_Noticia_Limpia": {"$exists": True},
        "$or": [
        {"es_economica_gpt": {"$exists": False}},
        {"es_economica_gpt": "Unknown"},
        {"es_economica_gpt": None}
    ],
    "Max_similarity": {"$exists": True, "$gt": 0.05},
    "character_count": {"$exists": True, "$gt": 500}
}

documents_for_similarity_calc = list(collection.find(query_limp).sort("Max_similarity", pymongo.DESCENDING))
print("# de Documentos a procesar:", len(documents_for_similarity_calc))

# Loop while both queries return non-empty results
while len(documents_for_similarity_calc) > 0:
    # Limpieza Noticias
    worker(documents=documents_for_similarity_calc, collection=collection)
    documents_for_similarity_calc = list(collection.find(query_limp))
    print("# de Documentos a procesar:", len(documents_for_similarity_calc))
