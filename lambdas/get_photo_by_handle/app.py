import json
from tempfile import mkdtemp
import logging
import sys
import boto3

#This part makes logging work locally when testing and in lambda cloud watch
if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    path = event['path']
    handle = path.split('/')[2]
    print(handle)
    try: 
        dynamodb = boto3.client('dynamodb', region_name='us-west-2')
        # This value would 
        table_name = 'twitter-profile-photos'
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                'handle': {'S': handle}
            }
        )
        if 'Item' in response:
           item = response['Item']
           url = item['url']['S']
    except Exception as e:
        logging.error(e)
    
    return  {
        "statusCode": 200,
        "body": url,
    }

