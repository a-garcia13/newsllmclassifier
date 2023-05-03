import os
import sys
import pymongo
from pymongo import MongoClient
import pandas as pd
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
import streamlit as st
from gpt4free import you, quora, Completion, Provider
import math
# Multiprocesamiento
import multiprocessing
import threading
import re

# Connect to MongoDB
client = MongoClient("mongodb://inst-newstic:7E69wh96tzcKjK5u3tnFHK7BwbpT2dbU61JsXxVsYdPNTuazAGNBZQPxNo6xaQcDJbxlsIKmiDrhACDbDy1fmg%3D%3D@inst-newstic.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@inst-newstic@")
db = client["newstic"]
collection = db["TIE_Modelo_Economia"]

def get_answer(question: str) -> str:
    # Set cloudflare clearance cookie and get answer from GPT-4 model
    try:
        result = you.Completion.create(prompt=question)
        escaped = result.text.encode('utf-8').decode('unicode-escape')
        if "Unable to fetch the response, Please try again." in escaped:
            tries = 0
            while "Unable to fetch the response, Please try again." in escaped:
                result = you.Completion.create(prompt=question)
                escaped = result.text.encode('utf-8').decode('unicode-escape')
                print(escaped)
                tries = tries + 1
                if tries == 20:
                    raise ValueError("max tries no answer")
        return escaped

    except Exception:
        # Return error message if an exception occurs
        try:
            token = quora.Account.create(logging=False)
            response = Completion.create(Provider.Poe, prompt=question, token=token, model='ChatGPT')
            return response
        except Exception as e:
            # Return error message if an exception occurs
            return (
                f'An error occurred: {e}. Please make sure you are using a valid cloudflare clearance token and user agent.'
            )


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
        prompt = f"Clasifica el siguiente artículo de noticias en si es o no una noticia económica, responder exclusivamente si o no, evitar cualquier otro tipo de texto. articulo: {article}"
        print("prompt", prompt)
        answer = get_answer(prompt)
        if "Unable to fetch the response, Please try again." in answer:
            tries = 0
            while "Unable to fetch the response, Please try again." in answer:
                answer = get_answer(prompt)
                print(answer)
                tries = tries + 1
                if tries == 20:
                    raise ValueError("max tries no answer")
        first_two = answer[:2]
        is_economic = update_es_economica_gpt(first_two)
        # Update the document in the collection
        document['es_economica_gpt'] = is_economic
        document['gpt_completa'] = answer
        update_all(collection, document)
        print("articulo:", article_id, "es:", is_economic, "y fue actualizado en la base de datos. respuesta de GTP:", answer, "Acotado:", first_two)
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


# Define the function to process documents concurrently
def process_documents_concurrently(worker, num_threads, collection, documents):
    print("Number of documents:", len(documents))
    print("Number of threads:", num_threads)

    # Split the document IDs into chunks for concurrent processing
    chunk_size = math.ceil(len(documents) / num_threads)
    print("Chunk size:", chunk_size)
    chunks = [documents[i:i + chunk_size] for i in range(0, len(documents), chunk_size)]
    print("Number of chunks:", len(chunks))

    # Create and start the worker threads
    threads = []

    for i in range(num_threads):
        print("Starting thread:", i, "with", len(chunks[i]), "documents")
        thread = threading.Thread(target=worker, args=(chunks[i], collection))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


query_limp = query = {
    "Desc_Noticia_Limpia": {"$exists": True},
    "es_economica_gpt": {"$exists": False},
    "gpt_completa": {"$exists": False},
    "Max_similarity": {"$exists": True, "$gt": 0.05},
    "character_count": {"$exists": True, "$gt": 500}
}

documents_for_similarity_calc = list(collection.find(query_limp).sort("Max_similarity", pymongo.DESCENDING))
print("# de Documentos a procesar:", len(documents_for_similarity_calc))

# Loop while both queries return non-empty results
while len(documents_for_similarity_calc) > 0:
    # Limpieza Noticias
    process_documents_concurrently(worker, multiprocessing.cpu_count(), collection, documents_for_similarity_calc)
    documents_for_similarity_calc = list(collection.find(query_limp))

    print("# de Documentos a procesar:", len(documents_for_similarity_calc))