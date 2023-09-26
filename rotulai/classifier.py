from pydantic import BaseModel
import json
import time
import random
import openai
import nltk
import string

from nltk import ngrams
from nltk.corpus import stopwords

from dotenv import load_dotenv
import os

#from topics import RH_TOPICS, MULTI_TOPICS


TEMP = 0.0
MODEL = "gpt-4-0613"

#nltk.download('stopwords')
#brazilian_stopwords = stopwords.words('portuguese')

#nltk.download('punkt')
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def classify(inp_text, TOPICS, temp):
    #paragraph = '\n.'.join(inp_text)
    sentences = inp_text

    sentiment_count = {"positive":0, "negative":0, "neutral":0, "mixed":0}
    functions_topics = [{
        "name":"print_topics",  
        "description":"A function that prints the given topics",
        "parameters":{
            "type": "object",
            "properties":{
                "topics":{
                    "type":"array",  
                    "items": {
                        "type": "string",
                        "enum": TOPICS
                    },
                    "description": "The Topics",  
            },
        },
        "required":["topics"],  
    }}]

    functions_sentiment = [{
                           "name": "print_sentment",
                           "description":"A function that prints given sentiment",
                           "parameters":{
                                "type": "object",
                                "properties":{
                                    "sentiment":{
                                        "type":"string",
                                        "enum": ["positive","negative","neutral", "mixed"],
                                        "description": " The sentiment",
                                },
                            },
                            "required":["sentiment"],
    }}]

    max_retries = 5
    backoff_factor = 0.5
    results = []
    #sentences = nltk.tokenize.sent_tokenize(paragraph)

    for sentence in sentences:
        messages = [{"role":"user", "content": sentence}]
        sentence_result = {"sentence": sentence}

        #words = nltk.word_tokenize(sentence)
        #words_filtered = [word for word in words if word not in brazilian_stopwords and word not in string.punctuation]
        
        #bi_grams = list(ngrams(words_filtered, 2))
        #tri_grams = list(ngrams(words_filtered, 3))

        #sentence_result["bi-grams"] = [" ".join(bi_gram) for bi_gram in bi_grams]
        #sentence_result["tri-grams"] = [" ".join(tri_gram) for tri_gram in tri_grams]

        # TOPICS
        functions = functions_topics
        function_call = {"name": "print_topics"}
        function_call["arguments"] = {"topics": TOPICS, "temperature": temp}
        
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
            functions=functions,
            function_call=function_call)
        function_call_response = response.choices[0].message["function_call"]
        argument = json.loads(function_call_response["arguments"])
        sentence_result["topics"] = argument["topics"]

        # SENTIMENT
        functions = functions_sentiment
        function_call = {"name": "print_sentment"}
        function_call["arguments"] = {"sentiments": ["positive","negative","neutral", "mixed"], "temperature": 0}
        
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
            functions=functions,
            function_call=function_call)
        function_call_response = response.choices[0].message["function_call"]
        argument = json.loads(function_call_response["arguments"])
        sentiment = argument["sentiment"]
        sentiment_count[sentiment] += 1
        sentence_result["sentiment"] = sentiment
        results.append(sentence_result)


    total_sentiments = sum(sentiment_count.values())
    percent_positive = (sentiment_count["positive"] / total_sentiments) * 100
    percent_negative = (sentiment_count["negative"] / total_sentiments) * 100

    SSCORE = percent_positive - percent_negative
    
    d = {"sentences": results, "sentiment count": sentiment_count, "SSCORE": SSCORE}
    return d



if __name__ == "__main__":
    sentences = []
    sentences.append("eu comprei uma passagem para voar de aviao.")
    sentences.append("Eu nunca vou querer entrar na politica")
    topics = ["veiculos", "carreira"]
    temp = 0
    r = classify(sentences, topics, temp)
    print(r)
