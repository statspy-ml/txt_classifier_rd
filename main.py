from fastapi import FastAPI, HTTPException
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


from topics import RH_TOPICS, MULTI_TOPICS
TEMP = 0.0
MODEL = "gpt-4-0613"

nltk.download('stopwords')
brazilian_stopwords = stopwords.words('portuguese')

nltk.download('punkt')
load_dotenv()  # take environment variables from .env.
openai.api_key = os.getenv('OPENAI_API_KEY')



app = FastAPI()

class Item(BaseModel):
    text: str
    mode: str

@app.post("/classify/")
async def classify_text(item: Item):
    paragraph = item.text
    mode = item.mode

    if mode not in ["topics", "sentiment", "both"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Choose 'topics', 'sentiment' or 'both'.")

    sentiment_count = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}

    functions_topics =[{
        "name":"print_topics",  
        "description":"A function that prints the given topics",
        "parameters":{
            "type": "object",
            "properties":{
                "topics":{
                    "type":"array",  
                    "items": {
                        "type": "string",
                        "enum": MULTI_TOPICS + RH_TOPICS
                    },
                    "description": "The Topics",  
            },
        },
        "required":["topics"],  
    }}]

    functions_sentiment =[{
        "name":"print_sentiment",
        "description":" A function that prints de given sentiment",
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

    sentences = nltk.tokenize.sent_tokenize(paragraph)

    for sentence in sentences:
        messages = [{"role":"user", "content": sentence}]
        sentence_result = {"sentence": sentence}


        
        words = nltk.word_tokenize(sentence)
        words_filtered = [word for word in words if word not in brazilian_stopwords and word not in string.punctuation]


        
        bi_grams = list(ngrams(words_filtered, 2))
        tri_grams = list(ngrams(words_filtered, 3))

        
        sentence_result["bi-grams"] = [" ".join(bi_gram) for bi_gram in bi_grams]
        sentence_result["tri-grams"] = [" ".join(tri_gram) for tri_gram in tri_grams]

        for m in ["topics", "sentiment"]:
            if mode == m or mode == "both":
                functions = functions_topics if m == "topics" else functions_sentiment
                function_call = {"name": "print_" + m}
                
                if m == "topics":
                    function_call["arguments"] = {
                        "topics": MULTI_TOPICS + RH_TOPICS,
                        "temperature": TEMP
                    }
                
                for attempt in range(max_retries):
                    try:
                        response = openai.ChatCompletion.create(
                            model=MODEL,
                            messages=messages,
                            functions=functions,
                            function_call=function_call, 
                        )
                        function_call_response = response.choices[0].message["function_call"]
                        argument = json.loads(function_call_response["arguments"])
                        sentence_result[m] = argument
                        break
                    except openai.api_errors.TimeoutError as e:
                        if attempt == max_retries - 1:  
                            raise e 

                        sleep_time = backoff_factor * (2 ** attempt) + random.random()
                        time.sleep(sleep_time)

            if m == "sentiment":
                    sentiment = argument["sentiment"]
                    sentiment_count[sentiment] += 1

        results.append(sentence_result)

    total_sentiments = sum(sentiment_count.values())
    percent_positive = (sentiment_count["positive"] / total_sentiments) * 100
    percent_negative = (sentiment_count["negative"] / total_sentiments) * 100

    SSCORE = percent_positive - percent_negative

    results.append({"final_sentiment_count": sentiment_count, "SSCORE": SSCORE})

    return results

