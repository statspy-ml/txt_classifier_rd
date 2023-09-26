from classifier import classify
import boto3
import botocore
import json
import random
import os
from datetime import datetime


BUCKET_NAME = "sent-persistence-s3-sent-data"


s3 = boto3.client('s3') 


# GETTING QUEUE
s3_prefix = f"analysis/queue/"
response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=s3_prefix)
if not response.get('Contents'):
    print("empty queue")
    exit()
random_object = random.choice(response['Contents'])
s3_object_key = random_object['Key']
key_to_remove = s3_object_key
response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_object_key)
json_content = json.loads(response['Body'].read().decode('utf-8'))
TOKEN = json_content['token']
BATCH_NAME = json_content['batch_name']
print(f"retrieving {BATCH_NAME} from token {TOKEN} ...")

# DELETE FROM QUEUE
s3.delete_object(Bucket=BUCKET_NAME, Key=key_to_remove)
print(f"{key_to_remove} removed from queue")

# GETTING CONFIG INFO
print(f"reading config ...")
s3_object_key = f"conf/{TOKEN}/{BATCH_NAME}.json"
response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_object_key)
json_content = json.loads(response['Body'].read().decode('utf-8'))
TOPICS = json_content['topics']
print(f"topics: {TOPICS}")

# GETTING INPUTS
s3_prefix = f"data/{TOKEN}/{BATCH_NAME}/sentences/"
response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=s3_prefix)
files = [os.path.basename(v['Key']) for v in response['Contents']]
num_files = len(files)
print(f"{num_files} inputs found...")

# GETTING SENTENCES FROM INPUTS
sentences = []
total_sentences = 0

for i, file in enumerate(files):
    print(f"reading file {i+1}/{num_files}")
    s3_object_key = f"data/{TOKEN}/{BATCH_NAME}/sentences/{file}"
    response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_object_key)
    json_content = json.loads(response['Body'].read().decode('utf-8'))
    file_sentences = json_content['sentences']
    num_sentences = len(file_sentences)
    total_sentences += num_sentences
    sentences += file_sentences
    print(f"{num_sentences} sentences added")
    
print(f"finished loading sentences, total {total_sentences}")

# PROCESSING
print("processing ...")
temp = 0
result = classify(sentences, TOPICS, temp)

# SAVING RESULT
ts = str(datetime.now()).split('.')[0].replace(' ','_')
s3_object_key = f"analysis/finished/{TOKEN}/{BATCH_NAME}/{ts}.json"
data = {"processing-date":ts, "token":TOKEN, "batch_name":BATCH_NAME, "topics":TOPICS, "results":result}
json_data = json.dumps(data)
s3.put_object(Bucket=BUCKET_NAME, Key=s3_object_key, Body=json_data, ContentType='application/json')
print(f"results saved at {s3_object_key}")

