import subprocess as sp
from time import sleep
import json


TOKEN = "user3"

def request(method, endpoint, data):
    template = open('request.txt').read()
    template = template.replace("%%METHOD%%", method)
    template = template.replace("%%ENDPOINT%%", endpoint)
    template = template.replace("%%DATA%%", data)
    return sp.getoutput(template)

def set_config(batch_name, topics):
    data = {"token":TOKEN, "batch-name":batch_name, "topics":topics}
    data = json.dumps(data)
    r = request("POST", "set-batch-config", data)
    return r.split('\n')[-1]

def send_sentences(batch_name, sentences):
    data = {"token":TOKEN, "batch-name":batch_name, "sentences":sentences}
    data = json.dumps(data)
    r = request("POST", "send-sentences", data)
    return r.split('\n')[-1]

def start_analysis(batch_name):
    data = {"token":TOKEN, "batch-name":batch_name}
    data = json.dumps(data)
    r = request("POST", "start-batch-analysis", data)
    return r.split('\n')[-1]

def results(batch_name):
    data = {"token":TOKEN, "batch_name":batch_name}
    data = json.dumps(data)
    r = request("POST", "retrieve_results", data)
    return r


if __name__=="__main__": 
    BATCH_NAME = "dataset4"

    # starting an analysis group
    print(f"setting parameters ({TOKEN}->{BATCH_NAME})")
    r = set_config(BATCH_NAME, ["compra", "feedback", "duvida"])
    print(r)

    # uploading sentences
    print("sending sentences")
    sentences = []
    sentences.append("ola, gostaria de comprar um Atenolol")
    sentences.append("o atendimento esta ruim demais, gostaria que fosse mais rapido")
    sentences.append("voces possuem Atenolol?")
    r = send_sentences(BATCH_NAME, sentences)
    print(r)

    # flagging for analysis
    print("starting analysis")
    r = start_analysis(BATCH_NAME)
    print(r)

    # retrieving results
    while 1:
        a = input("retrieve results?(Y/n)")
        if a == 'n':
            break
        r = results(BATCH_NAME)
        print(r)
