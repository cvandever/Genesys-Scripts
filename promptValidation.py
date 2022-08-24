#!/user/bin/python

import json
import time
import requests
from pprint import pprint
import PureCloudPlatformClientV2 as v2
import pandas as pd
import os

prompts_list = []
prompts_dict = []
prompt_titles = []



GENESYS_CLOUD_CLIENT_ID = os.getenv('GENESYS_CLOUD_CLIENT_ID_PE')
GENESYS_CLOUD_CLIENT_SECRET = os.getenv('GENESYS_CLOUD_CLIENT_SECRET_PE')

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


def get_prompts():
    url = f"{api_url}architect/prompts?pageSize=100&sortOrder=asc"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    prompts_list.append(json.loads(response.text))
    data = json.loads(response.text)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    time.sleep(0.2)
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}architect/prompts?pageSize=100&pageNumber={page_number}&sortOrder=asc"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        prompts_list.append(json.loads(response.text))
        time.sleep(0.2)

    
    for prompts in prompts_list:
        for prompt in prompts['entities']:

            prompt_name = prompt.get('name')
            prompt_resources = prompt.get('resources')
            resources = []
            prompt_titles.append({'name': prompt_name})
            for resource in prompt_resources:
                lang = resource.get('id')
                if lang == 'en-us' or lang == 'es-us':
                    if lang == 'en-us':
                        lang = 'English'
                    else:
                        lang = 'Spanish'
                    upload_status = resource.get('uploadStatus')
                    if upload_status == 'transcoded':
                        upload_status = 'Recorded'
                        duration = resource.get('durationSeconds')
                    else:
                        upload_status = "*Not Recorded*"
                        duration = 0
                    resource_list = {'language': lang, 'status': upload_status,'duration': duration}
                    resources.append(resource_list)
                
            final_prompt = {'name': prompt_name, 'resources': resources}
            prompts_dict.append(final_prompt)

    #Removed with Descriptions
    """
    #to remove duplicated values in name and prompt Description columns
    mergedf['Duplicated'] = mergedf.duplicated(subset=["name","promptDescription"],keep="first")
    mergedf.loc[mergedf["Duplicated"] == True, ["name","promptDescription"]] = np.NaN
    mergedf.drop("Duplicated",axis=1, inplace=True)

    for name in mergedf['name'].unique():
    # find indices and add one to account for header
        dup_name=mergedf.loc[mergedf['name']==name].index.values + 1

        if len(dup_name) <2: 
            pass
            # do not merge cells if there is only one name
        else:   # merge cells using the first and last indices
            worksheet.merge_range(dup_name[0], 0, dup_name[-1], 0, mergedf.loc[dup_name[0],'name'], merge_format)
    
    """

def create_excel():
    outer_df = pd.json_normalize(prompt_titles)
    inner_df = pd.json_normalize(prompts_dict,record_path="resources",meta="name")
    inner_df = inner_df[["name","language","status","duration"]]

    mergedf = outer_df.merge(inner_df,on="name")
    rows = len(mergedf)
    rows = str(rows)
    writer = pd.ExcelWriter("PE_GenesysPrompts.xlsx", engine="xlsxwriter")
    
    mergedf.to_excel(writer, sheet_name="Prompts", index=False)
    workbook = writer.book
    worksheet = writer.sheets['Prompts']
    merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 2, 'bold': True})
    merge_format.set_top()
    merge_format.set_bottom()
    resource_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 2})
    resource_format.set_top()
    resource_format.set_bottom()
    

    
    worksheet.set_column("B:D",None,resource_format)
      
    worksheet.set_column("A:A",None,merge_format)


    
    format_english = workbook.add_format({'bg_color':'#d1f3fa'})
    format_spanish = workbook.add_format({'bg_color':'#dcefdd'})
    format_recorded = workbook.add_format({'bg_color':'#E8E8E8'})
    format_not_recorded = workbook.add_format({'bold': True, 'font_color': '#ff3333'})
    
    worksheet.conditional_format(f"A2:B{rows}",{'type': 'formula', 'criteria': '=$B2="English"', 'format': format_english})
    worksheet.conditional_format(f"A2:B{rows}",{'type': 'formula', 'criteria': '=$B2="Spanish"', 'format': format_spanish})
    worksheet.conditional_format(f"C2:D{rows}",{'type': 'formula', 'criteria': '=$C2="Recorded"', 'format': format_recorded})
    worksheet.conditional_format(f"C2:D{rows}",{'type': 'formula', 'criteria': '=$C2="*Not Recorded*"', 'format': format_not_recorded})

    table_headers = [{'header': 'Prompt Name'}, {'header': 'Language'}, {'header': 'Status'}, {'header': 'Duration'}]
 
    worksheet.add_table(f"A1:D{rows}",{'style': 'Table Style Light 11', 'columns': table_headers})
    writer.save()



def main():    
    get_api_token()
    get_prompts()
    create_excel()

if __name__ == '__main__':
    main()