import json
from tempfile import mkdtemp
import logging
import boto3

#This part makes logging work locally when testing and in lambda cloud watch
if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
    try: 
        logging.info(event)
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('twitter-profile-photos')
        
        count = int(event['queryStringParameters'].get('count', 10))
        # ideally, scans should be avoided since it is costly. 
        next_key = event['queryStringParameters'].get('nextPageKey', None)
        if next_key:
            response = table.scan(ExclusiveStartKey=next_key, Limit=count)
        else:
            response = table.scan(Limit=count)
            
        handles = [item['handle'] for item in response['Items']]
        next_page_key = response.get('LastEvaluatedKey', None)
        logging.info('handles: %s', handles)

    except Exception as e:
        logging.error(e)
        return {
            "statusCode": 500,
            "body": "Error getting handles from DynamoDB"
        }
        
    response_body = {
        "handles": handles
    }
    
    if next_page_key:
        response_body['nextPageKey'] = next_page_key
    
    return  {
        "statusCode": 200,
        "body": json.dumps(response_body),
        "headers": {
            "Content-Type": "application/json"
        }
    }
