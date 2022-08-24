import PureCloudPlatformClientV2 as v2
import requests
import json
import os
import pprint

log = []

#GENESYS_CLOUD_CLIENT_ID_PE
#GENESYS_CLOUD_CLIENT_SECRET_PE

#environment variables for OAuth keys
GENESYS_CLOUD_CLIENT_ID = os.getenv('GENESYS_CLOUD_CLIENT_ID_CE')
GENESYS_CLOUD_CLIENT_SECRET = os.getenv('GENESYS_CLOUD_CLIENT_SECRET_CE')



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


#creating custom prompt, creating custom prompt resource. nesting resource in prompt with return to prompts_data.
def create_custom_prompts(prompt_name,prompt_script,resources):
    prompt_resources = []
    prompt_url = f"{api_url}architect/prompts"
    prompt_payload = json.dumps({
        "name": prompt_name,
        "description": prompt_script,
        "resources": []
        })
    prompt_response = requests.request("POST", prompt_url, headers=headers, data=prompt_payload)
    prompt_text = json.loads(prompt_response.text)
    prompt_id = prompt_text.get('id')


    for resource in resources:
        resource_url = f"{api_url}architect/prompts/{prompt_id}/resources"
        resource_payload = json.dumps({
            "name": resource,
            "language": resource,
            "ttsString": prompt_script,
            "text": prompt_script
            })
        resource_response = requests.request("POST", resource_url, headers=headers, data=resource_payload)
        resource_text = json.loads(resource_response.text)
        prompt_resources.append(resource_text)

    prompt_text['resources'] = prompt_resources
    prompts_data = prompt_text
    log.append(prompts_data)
    if prompt_response.status_code < 300:
        return f"{prompt_response.status_code} - Success"
    else:
        return f"{prompt_response.status_code} - {prompts_data['message']}"

def set_prefix():
    global generic_prompts, prefix

    prefix = input("Pre-fix for Generic Prompts (ex. Oregon_SouthPC  |  Oregon_Geopod_NW) \n\t--")


    generic_prompts = {
    f"{prefix}_911":                    "If this is a medical emergency, hang up and dial 911.",
    f"{prefix}_CCB_NOT_Offered":        "Please continue to hold for the next available caregiver.",
    f"{prefix}_CCBANI1":                "If you would like us to call you back at",
    f"{prefix}_CCBANI2":                "press 1. To use a different callback number, press 2.",
    f"{prefix}_CCBDupReq":              "You currently have a pending call back request. You may opt to cancel your previous request and return to waiting on hold however you will be placed farther back in line. Press 1 to cancel your original request and be placed back on hold. Otherwise, hang up and your call will be returned in the order it was originally received.",
    f"{prefix}_CCBError":               "We are unable to process your callback request, please hold for the next available caregiver.",
    f"{prefix}_CCBInvalidDigits":       "You did not enter a valid 10 digit number.",
    f"{prefix}_CCBNoANI":               "Please enter your 10-digit callback number, beginning with the area code.",
    f"{prefix}_CCBScheduled":           "Thank You. The next available caregiver will return your call in the order it was received.",
    f"{prefix}_ClsdEmergency":          "We are temporarily unavailable to take your call due to a building emergency. If you are a physician, care provider or care facility with an urgent matter and would like to speak to the on-call provider, press 1.",
    f"{prefix}_ClsdHoliday":            "We are currently closed in observance of the holiday. If you are a physician, care provider or care facility with an urgent matter and would like to speak to the on-call provider, press 1.",
    f"{prefix}_ClsdWeather":            "We are temporarily unavailable to take your call due to inclement weather. Please visit our website at www.providence.org/locations for up to date clinic hours and information. If you are a physician, care provider or care facility with an urgent matter and would like to speak to the on-call provider, press 1.",
    f"{prefix}_NurseAdvice":            "If you would like to speak with our advice nurse, remain on the line. Our after-hours nursing team can assist with care advice and connect with an on-call physician when needed.",
    f"{prefix}_Provider_Option":        "If you are a physician calling to speak to one of our providers, press 1",
    f"{prefix}_Q1st":                   "All of our caregivers are currently assisting other callers. Please remain on the line for the next available caregiver.",
    f"{prefix}_Q2nd":                   "Our caregivers continue to assist other callers, please remain on the line.",
    f"{prefix}_QMyChart":               "Did you know you can use MyChart to request or cancel an appointment or request a medication refill. Ask your caregiver how to activate your account.",
    f"{prefix}_QPositionCCBOffer":      "If you'd like us to hold your place in line and call you back press 1. Otherwise remain on the line for the next available caregiver.",
    f"{prefix}_Quality":                "This call may be monitored or recorded for quality or training purposes.",
    f"{prefix}_RxInfo":                 "For prescription refills, contact your pharmacy directly and allow 72 business hours to process your request.",
    f"{prefix}_SpanishOpt1":            "Para continuar en español, presione 1.",
    f"{prefix}_TechnicalDifficulty":    "We are currently experiencing some technical difficulties, please try your call at a later time. Thank you.",
    f"{prefix}_Unavailable":            "We are temporarily unavailable to take your call. If you are a physician, care provider or care facility with an urgent matter and would like to speak to the on-call provider, press 1. For all other non-urgent request, please try your call again later."
        }

def create_log():
    out_log = pprint.pformat(log)
    with open(f'{prefix}_PromptsLog.txt', 'w') as f:
        f.write(out_log)
    
def upload_prompts(prompts:dict):
    #Languages can be added in resources
    resources = ['en-us', 'es-us']
    for k,v in prompts.items():
        status = create_custom_prompts(k,v,resources)
        print(f"{k} - {status} \n")
    



def main():    
    get_api_token()
    set_prefix()
    upload_prompts(generic_prompts)
    create_log()
    
    

if __name__ == '__main__':
    main()
    