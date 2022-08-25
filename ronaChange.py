import PureCloudPlatformClientV2 as v2
import requests
import json
import os
import pprint
import numpy as np

#GENESYS_CLOUD_CLIENT_ID_PE
#GENESYS_CLOUD_CLIENT_SECRET_PE

#environment variables for OAuth keys
GENESYS_CLOUD_CLIENT_ID = os.getenv('GENESYS_CLOUD_CLIENT_ID_CE')
GENESYS_CLOUD_CLIENT_SECRET = os.getenv('GENESYS_CLOUD_CLIENT_SECRET_CE')

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'to_json'):
            return obj.to_json()
        if isinstance(obj, np.integer):
            return int(obj)
        return json.JSONEncoder.default(self, obj)


def get_api_token():
    #Setting the Region 
    region = v2.PureCloudRegionHosts.us_west_2
    v2.configuration.host = region.get_api_host()
    #with Client Credntials Create a token object
    apiclient = v2.api_client.ApiClient().get_client_credentials_token(GENESYS_CLOUD_CLIENT_ID, GENESYS_CLOUD_CLIENT_SECRET)
    global apitoken
    #collect token from token object
    apitoken = apiclient.access_token
    global headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'authorization': f'Bearer {apitoken}'
        }    

api_url = "https://api.usw2.pure.cloud/api/v2/"


def get_QueueList():
    queue_list = []
    url = f"{api_url}routing/queues?pageSize=100"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    queue_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}routing/queues?pageSize=100&pageNumber={page_number}"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        queue_list.append(json.loads(response.text))


    for list in queue_list:
        for queue in list['entities']:
            queue_id = queue.get('id')
            queue_name = queue.get('name')
            get_queue(queue_id)
            print(f"---Changing the Alerting Timeout for {queue_name}  \n\n")     


def get_queue(id):
    url = f"{api_url}routing/queues/{id}"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    try:
        data['mediaSettings']['call']['alertingTimeoutSeconds'] = 99
    except KeyError as e:
        print(f"Not Seeing a {e.args[0]}")
    queue_payload = json.dumps(data,cls=JSONEncoder)
    put_queue(id,queue_payload)

def put_queue(id,payload):
    url = f"{api_url}routing/queues/{id}"
    payload=payload
    requests.request("PUT", url, headers=headers, data=payload)
            

def main():
    get_api_token()
    get_QueueList()


if __name__ == '__main__':
    main()