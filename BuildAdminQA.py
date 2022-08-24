#!/user/bin/python

import json
import requests, re
from pprint import pprint
import PureCloudPlatformClientV2 as v2
import pandas as pd
from numpy import NaN
from datetime import datetime
import os


sites = []
locations = []
groups = []
queues = []
emergency_groups = []
schedules = []
schedule_groups = []
dids = []
users = []
roles = []
prompts = []

user_ids = []
users_roles = []


#environment variables for OAuth keys
GENESYS_CLOUD_CLIENT_ID = os.getenv('GENESYS_CLOUD_CLIENT_ID_PE')
GENESYS_CLOUD_CLIENT_SECRET = os.getenv('GENESYS_CLOUD_CLIENT_SECRET_PE')

clinic_1 = {'clinicTitle': 'PMG_MMC_Hillcrest'}
clinic_2 = {'clinicTitle': 'PMG_Medford_Pediatrics'}
clinic_3 = {'clinicTitle': 'PMG_South_Call_Center'}
clinic_4 = {'clinicTitle': 'PMG_Camas'}
clinic_5 = {'clinicTitle': 'PMG_Gateway_Family'}
clinic_6 = {'clinicTitle': 'PMG_Gateway_Internal'}
clinic_7 = {'clinicTitle': 'PMG_Mill_Plain_Family'}
clinic_8 = {'clinicTitle': 'PMG_Mill_Plain_Walkin'}

clinics = [clinic_1,clinic_2,clinic_3]


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


def regex_search(iterable,query,results,title):
    result = []     
    regex_string = re.escape(query)
    for iter in iterable:
        if re.search(regex_string,iter['name'],re.IGNORECASE):
            result.append(iter)
    results.update({title: result})

            
def search_for_clinic():
    for clinic in clinics:
        regex_search(sites,clinic['clinicTitle'],clinic,'sites')
        regex_search(locations,clinic['clinicTitle'],clinic,'locations')
        regex_search(groups,clinic['clinicTitle'],clinic,'groups')
        regex_search(queues,clinic['clinicTitle'],clinic,'queues')
        regex_search(emergency_groups,clinic['clinicTitle'],clinic,'emergencyGroups')
        regex_search(schedules,clinic['clinicTitle'],clinic,'schedules')
        regex_search(schedule_groups,clinic['clinicTitle'],clinic,'scheduleGroups')
        regex_search(dids,clinic['clinicTitle'],clinic,'dids')
        regex_search(prompts,clinic['clinicTitle'],clinic,'prompts')

def get_sites():
    site_list = []
    url = f"{api_url}telephony/providers/edges/sites?pageSize=100"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    site_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}telephony/providers/edges/sites?pageSize=100&pageNumber={page_number}"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        site_list.append(json.loads(response.text))

    for list in site_list:
        for site in list['entities']:
            id = site.get('id')
            name = site.get('name')
            location = site['location'].get('name')
            caller_name = site.get('callerName')
            caller_id = site.get('callerId')
            sites.append({'name': name, 'id': id, 'linkedLocation': location, 'callerName': caller_name, 'callerId': caller_id})


def get_locations():
    location_list = []
    url = f"{api_url}locations?pageSize=100"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    location_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    if page_count == None:
        page_count = 1
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}locations?pageSize=100&pageNumber={page_number}"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        location_list.append(json.loads(response.text))

    for list in location_list: 
        for location in list['entities']:
            id = location.get('id')
            name = location.get('name')
            verified = location.get('addressVerified')
            city = location['address'].get('city')
            state = location['address'].get('state')
            street1 = location['address'].get('street1')
            street2 = location['address'].get('street2')
            zipcode = location['address'].get('zipcode')
            address = f"{street1} {street2}  {city}, {state} {zipcode}"
            try:
                elin = location['emergencyNumber'].get('number')
            except KeyError:
                elin = "*No Emergency Number for location*"

            locations.append({'name': name, 'id': id, 'address': address, 'elin': elin, 'addressVerified': verified})



def get_groups():
    group_list = []
    
    url = f"{api_url}groups?pageSize=100"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    group_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}groups?pageSize=100&pageNumber={page_number}"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        group_list.append(json.loads(response.text))

    for list in group_list:
        for group in list['entities']:
            owners = []
            id = group.get('id')
            name = group.get('name')
            addresses = group.get('addresses')
            if addresses != None:
                for address in addresses:
                    #lazy, if group has extension and phone number it will get last.
                    did = address.get('display')
            else: 
                did = "*No DID or Extension"
            member_count = group.get('memberCount')
            owner_ids = group.get('owners')
            if owner_ids != None:
                for owner in owner_ids:           
                    owners.append(owner.get('id'))
            groups.append({'name': name, 'id': id, 'phoneNumber': did, 'memberCount': member_count, 'owners': owners})



def get_queues():
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
            id = queue.get('id')
            name = queue.get('name')
            member_count = queue.get('memberCount')
            division = queue['division'].get('name')
            caller_name = queue.get('callingPartyName')
            caller_id = queue.get('callingPartyNumber')
            try:
                queue_flow = queue['queueFlow'].get('name')
            except KeyError:
                queue_flow = "*No Queue Flow associated*"
            acw_settings = queue.get('acwSettings')
            call = queue['mediaSettings'].get('call')
            queues.append({'name': name, 'id': id,'division': division,'memberCount': member_count, 'callingPartyName': caller_name, 'callingPartyNumber': caller_id, 'queueFlow': queue_flow, 'acwSettings': acw_settings, 'call': call})


def get_emergency_groups():
    emergency_group_list = []
    url = f"{api_url}architect/emergencygroups?pageSize=100"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    emergency_group_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}architect/emergencygroups?pageSize=100&pageNumber={page_number}"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        emergency_group_list.append(json.loads(response.text))

    for list in emergency_group_list:
        for emergency_group in list['entities']:
            name = emergency_group.get('name')
            division = emergency_group['division'].get('name')
            emergency_groups.append({'name': name, 'division': division})


def get_schedules():
    schedule_list = []
    url = f"{api_url}architect/schedules?pageSize=100"
    org_schedules_payload={}
    response = requests.request("GET", url, headers=headers, data=org_schedules_payload)
    data = json.loads(response.text)
    schedule_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')

    while page_count != page_number:
        page_number += 1
        url = f"{api_url}architect/schedules?pageSize=100&pageNumber={page_number}"
        response = requests.request("GET", url, headers=headers, data=org_schedules_payload)
        schedule_list.append(json.loads(response.text))

    for list in schedule_list:
        for schedule in list['entities']:
            id = schedule.get('id')
            name = schedule.get('name')
            division = schedule['division'].get('name')
            start = schedule.get('start')
            start = change_datetime(start)
            end = schedule.get('end')
            end = change_datetime(end)
            frequency = schedule.get('rrule')
            schedules.append({'name': name, 'id': id, 'division': division, 'start': start, 'end': end, 'frequency': frequency})

    
        
def change_datetime(time):
    date_time = datetime.strptime(time,'%Y-%m-%dT%H:%M:%S.%f')
    sched_date = date_time.date().strftime('%m/%d/%Y')
    sched_time = date_time.time().strftime('%I:%M %p')
    time = f'{sched_date}   @   {sched_time}' 
    return time
        

def get_schedule_groups():
    schedule_group_list = []
    url = f"{api_url}architect/schedulegroups?pageSize=100"
    org_schedules_payload={}
    response = requests.request("GET", url, headers=headers, data=org_schedules_payload)
    data = json.loads(response.text)
    schedule_group_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')

    while page_count != page_number:
        page_number += 1
        url = f"{api_url}architect/schedulegroups?pageSize=100&pageNumber={page_number}"
        response = requests.request("GET", url, headers=headers, data=org_schedules_payload)
        schedule_group_list.append(json.loads(response.text))

    for list in schedule_group_list:
        for schedule_group in list['entities']:
            open_schedule_ids = []
            closed_schedule_ids = []
            holiday_schedule_ids = []
            id = schedule_group.get('id')
            name = schedule_group.get('name')
            division = schedule_group['division'].get('name')
            time_zone = schedule_group.get('timeZone')
            open_schedules = schedule_group.get('openSchedules')
            if open_schedules != None:
                for open_schedule in open_schedules:
                    open_schedule_ids.append(open_schedule.get('id'))

            closed_schedules = schedule_group.get('closedSchedules')
            if closed_schedules != None:
                for closed_schedule in closed_schedules:
                    closed_schedule_ids.append(closed_schedule.get('id'))

            holiday_schedules = schedule_group.get('holidaySchedules')
            if holiday_schedules != None:
                for holiday_schedule in holiday_schedules:
                    holiday_schedule_ids.append(holiday_schedule.get('id'))

            schedule_groups.append({'name': name, 'id': id,'division': division, 'timeZone': time_zone, 'openSchedules': open_schedule_ids, 'closedSchedules': closed_schedule_ids, 'holidaySchedules': holiday_schedule_ids})


def get_dids():
    did_list = []
    url = f"{api_url}telephony/providers/edges/dids?pageSize=100"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    did_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}telephony/providers/edges/dids?pageSize=100&pageNumber={page_number}&sortOrder=asc"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        did_list.append(json.loads(response.text))

    for list in did_list:
        for did in list['entities']:
            number = did.get('phoneNumber')
            owner = did['owner'].get('name')
            owner_type = did.get('ownerType')
           
            dids.append({'phoneNumber': number, 'name': owner, 'ownerType': owner_type})



def get_all_users():
    user_list = []
    url = f"{api_url}users?pageSize=100&expand=locations,groups"
    payload={}
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    user_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}users?pageSize=100&pageNumber={page_number}&expand=locations,groups"
        payload={}
        response = requests.request("GET", page_url, headers=headers, data=payload)
        user_list.append(json.loads(response.text))

    for list in user_list:
        for user in list['entities']:
            location_ids = []
            group_ids = []
            id = user.get('id')
            name = user.get('name')
            division = user['division'].get('name')
            email = user.get('email')
            addresses = user.get('addresses')
            for address in addresses:
                extensions = address.get('extension')
            title = user.get('title')
            locations = user.get('locations')
            for location in locations:
                location_ids.append(location['locationDefinition'].get('id'))
            groups = user.get('groups')
            for group in groups:
                group_ids.append(group.get('id'))

            users.append({'name': name, 'id': id, 'division': division, 'email': email, 'extension': extensions, 'title': title, 'locations': location_ids, 'groups': group_ids})



def get_prompts():
    prompt_list = []
    url = f"{api_url}architect/prompts?pageSize=100&sortOrder=asc"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    prompt_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}architect/prompts?pageSize=100&pageNumber={page_number}&sortOrder=asc"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        prompt_list.append(json.loads(response.text))

    
    for list in prompt_list:
        for prompt in list['entities']:
            prompt_name = prompt.get('name')
            prompt_description = prompt.get('description')
            prompts.append({'name': prompt_name, 'description': prompt_description})


def get_site_phones():
    for clinic in clinics:       
        clinic_sites = clinic.get('sites')
        for site in clinic_sites:
            site_phones = []
            site_id = site.get('id')
            url = f"{api_url}telephony/providers/edges/phones?pageSize=100&site.id={site_id}"
            payload={}  
            response = requests.request("GET", url, headers=headers, data=payload)
            data = json.loads(response.text)
            phones = data['entities']
            for phone in phones:
                site_phones.append(phone.get('name'))
            site.update({'sitePhones': site_phones})



def get_queue_members():
    for clinic in clinics: 
        clinic_queues = clinic.get('queues')
        for queue in clinic_queues:
            queue_members = []
            id = queue.get('id')

            url = f"{api_url}routing/queues/{id}/members?pageSize=100"
            payload={}  
            response = requests.request("GET", url, headers=headers, data=payload)
            data = json.loads(response.text)
            members = data['entities']
            for member in members:
                queue_members.append(member.get('name'))
            queue.update({'queueMembers': queue_members})
            


def get_users_roles(iterable):
    for iter in iterable:
        id = iter.get('id')
        roles = []
        url = f"{api_url}authorization/subjects/{id}"
        payload={}  
        response = requests.request("GET", url, headers=headers, data=payload)
        data = json.loads(response.text)
        try:
            for role in data['grants']:
                division = role['division'].get('name')
                role_name = role['role'].get('name')
                roles.append(f'{role_name} - {division}')
        except KeyError:
            roles = '*No Roles Set*'

        #Getting Default phones for user

        url = f"{api_url}users/{id}/station"
        payload={}  
        response = requests.request("GET", url, headers=headers, data=payload)
        data = json.loads(response.text)
        try:
            default_phone = data['defaultStation'].get('name')
        except KeyError:
            default_phone = '*Default not Set*'

        iter.update({'defaultPhone': default_phone, 'roles': roles})


def get_group_members():
    for clinic in clinics:
        clinic_groups = clinic.get('groups')
        for group in clinic_groups:
            group_members = []
            id = group.get('id')

            url = f"{api_url}groups/{id}/individuals"
            payload={}  
            response = requests.request("GET", url, headers=headers, data=payload)
            data = json.loads(response.text)
            members = data['entities']
            owners = group.get('owners')
            for user in users: 
                for member in members: 
                    member_id = member.get('id')                
                    if member_id == user['id']:
                        group_members.append(user.get('name'))
            
                for owner in owners: 
                    if owner == user['id']:
                        owners.append(user.get('name'))
                        owners.remove(owner)
            group.update({'groupMembers': group_members})
            
            

def location_membership():
    for clinic in clinics:
        clinic_members = []
        clinic_locations = clinic.get('locations')
        for location in clinic_locations:
            id = location.get('id')
            location_members = []
            for user in users:
                user_locations = user.get('locations')
                for user_location in user_locations:
                    if user_location == id:
                        location_members.append(user.get('name'))
                        clinic_members.append(user)
            location.update({'locationMembers': location_members})
        get_users_roles(clinic_members)
        clinic.update({'clinicMembers': clinic_members})
        

def user_membership():
    for clinic in clinics:
        clinic_members = clinic.get('clinicMembers')
        for member in clinic_members:
            clinic_groups = member.get('groups')
            clinic_locations = member.get('locations')
            for group in groups: 
                for clinic_group in clinic_groups:               
                    if clinic_group == group['id']:
                        clinic_groups.append(group.get('name'))
                        clinic_groups.remove(clinic_group)
            for location in locations:            
                for clinic_location in clinic_locations:              
                    if clinic_location == location['id']:
                        clinic_locations.append(location.get('name'))
                        clinic_locations.remove(clinic_location)


def schedule_names():
    for clinic in clinics:
        clinic_schedule_groups = clinic.get('scheduleGroups')
        for schedule_group in clinic_schedule_groups:
            open_schedules = schedule_group.get('openSchedules')
            closed_schedules = schedule_group.get('closedSchedules')
            holiday_schedules = schedule_group.get('holidaySchedules')
            for schedule in schedules:
                schedule_id = schedule.get('id')
                for open_schedule in open_schedules:
                    if schedule_id == open_schedule:
                        open_schedules.append(schedule.get('name'))
                        open_schedules.remove(open_schedule)
                for closed_schedule in closed_schedules:
                    if schedule_id == closed_schedule:
                        closed_schedules.append(schedule.get('name'))
                        closed_schedules.remove(closed_schedule)
                for holiday_schedule in holiday_schedules:
                    if schedule_id == holiday_schedule:
                        holiday_schedules.append(schedule.get('name'))
                        holiday_schedules.remove(holiday_schedule)


def create_excel():
    for clinic in clinics:    
        site_location_tab = 0
        group_queue_tab = 0
        schedules_schedgroup_tab = 0

        clinic_group = 'Oregon Group 7'
        clinic_name = clinic.get('clinicTitle')
        writer = pd.ExcelWriter(f"{clinic_name}_{clinic_group}_Admin_QA.xlsx", engine="xlsxwriter")

        #Create site db to prepare for excel
        site_df = pd.json_normalize(clinic,'sites', record_prefix='site - ').explode('site - sitePhones').drop('site - id',axis=1)
        #after exploding list clean up duplicates
        site_df['Duplicated'] = site_df.duplicated(subset=['site - name','site - callerId', 'site - callerName','site - linkedLocation'],keep="first")
        site_df.loc[site_df["Duplicated"] == True, ['site - name','site - callerId', 'site - callerName','site - linkedLocation']] = NaN
        site_df.drop("Duplicated",axis=1, inplace=True)
        #Send db to excel file on sheet name sites and locations
        
        site_df.to_excel(writer, sheet_name="Sites & Locations", index=False)
        site_len = len(site_df) + 3
        site_location_tab += site_len
        #Create location db to prepare for excel


        location_df = pd.json_normalize(clinic,'locations', record_prefix='location - ').explode('location - locationMembers').drop('location - id',axis=1)

        location_df['Duplicated'] = location_df.duplicated(subset=['location - name','location - address', 'location - elin','location - addressVerified'],keep="first")
        location_df.loc[location_df["Duplicated"] == True, ['location - name','location - address', 'location - elin','location - addressVerified']] = NaN
        location_df.drop("Duplicated",axis=1, inplace=True)

        location_df.to_excel(writer, sheet_name="Sites & Locations", index=False, startrow=site_len)


        #for each group create db to prepare for excel
        for group in clinic['groups']:
            
            if group['groupMembers'] != [] and group['owners'] != []:
                group_df = pd.json_normalize(group).explode('owners').drop(['id','groupMembers'],axis=1)
                group_members_df = pd.json_normalize(group,'groupMembers')
                group_members_df.columns = ['groupMembers']

                group_df['Duplicated'] = group_df.duplicated(subset=['name','phoneNumber','memberCount'],keep="first")
                group_df.loc[group_df["Duplicated"] == True, ['name','phoneNumber','memberCount']] = NaN
                group_df.drop("Duplicated",axis=1, inplace=True)

                group_df.reset_index(inplace=True, drop=True)
                group_df = pd.concat([group_df,group_members_df],axis=1)
                group_len = len(group_df) + 2

            else:
                group_df = pd.json_normalize(group).explode('owners').explode('groupMembers').drop('id',axis=1)

                group_df['Duplicated'] = group_df.duplicated(subset=['name','phoneNumber','memberCount','owners'],keep="first")
                group_df.loc[group_df["Duplicated"] == True, ['name','phoneNumber','memberCount','owners']] = NaN
                group_df.drop("Duplicated",axis=1, inplace=True)

            group_df.to_excel(writer, sheet_name="Groups & Queues", index=False,startrow=group_queue_tab)
            group_queue_tab += group_len


        for queue in clinic['queues']:

            queue_df = pd.json_normalize(queue).explode('queueMembers').drop('id',axis=1)

            queue_df['Duplicated'] = queue_df.duplicated(subset=['name','division', 'memberCount','callingPartyName','callingPartyNumber', 'queueFlow', 'acwSettings.wrapupPrompt','acwSettings.timeoutMs','call.alertingTimeoutSeconds', 'call.serviceLevel.percentage','call.serviceLevel.durationMs'],keep="first")
            queue_df.loc[queue_df["Duplicated"] == True, ['name','division', 'memberCount','callingPartyName','callingPartyNumber', 'queueFlow', 'acwSettings.wrapupPrompt','acwSettings.timeoutMs','call.alertingTimeoutSeconds', 'call.serviceLevel.percentage','call.serviceLevel.durationMs']] = NaN
            queue_df.drop("Duplicated",axis=1, inplace=True)
            queue_len = len(queue_df) + 2
            queue_df.to_excel(writer, sheet_name="Groups & Queues", index=False, startrow=group_queue_tab)
            group_queue_tab += queue_len


        did_df = pd.json_normalize(clinic,'dids', record_prefix='DIDs - ')
        did_len = len(did_df) + 3
        did_df.to_excel(writer, sheet_name="DIDs, Emer Groups & Prompts", index=False)


        emergency_group_df = pd.json_normalize(clinic,'emergencyGroups', record_prefix='Emer Group - ') 
        emer_group_len = len(emergency_group_df) + did_len + 3
        emergency_group_df.to_excel(writer, sheet_name="DIDs, Emer Groups & Prompts", index=False, startrow=did_len)


        prompt_df = pd.json_normalize(clinic,'prompts', record_prefix='Prompt - ')
        prompt_df.to_excel(writer, sheet_name="DIDs, Emer Groups & Prompts", index=False, startrow=emer_group_len)


        schedule_df = pd.json_normalize(clinic,'schedules', record_prefix='Schedule - ').drop('Schedule - id',axis=1)
        schedule_len = len(schedule_df) + 3
        schedule_df.to_excel(writer, sheet_name="Schedules & Schedule Groups", index=False)
        schedules_schedgroup_tab += schedule_len


        for sched_group in clinic['scheduleGroups']:

            if sched_group['closedSchedules'] != [] and sched_group['holidaySchedules'] != []:
                schedule_group_df = pd.json_normalize(sched_group).explode('openSchedules').drop(['id','closedSchedules','holidaySchedules'],axis=1)

                schedule_group_df['Duplicated'] = schedule_group_df.duplicated(subset=['name','division', 'timeZone'],keep="first")
                schedule_group_df.loc[schedule_group_df["Duplicated"] == True, ['name','division', 'timeZone']] = NaN
                schedule_group_df.drop("Duplicated",axis=1, inplace=True)

                schedule_group_closed_df = pd.json_normalize(sched_group,record_path='closedSchedules')
                schedule_group_closed_df.columns = ['closedSchedules']

                schedule_group_holiday_df = pd.json_normalize(sched_group,record_path='holidaySchedules')
                schedule_group_holiday_df.columns = ['holidaySchedules']

                schedule_group_df.reset_index(inplace=True, drop=True)
                schedule_group_df = pd.concat([schedule_group_df,schedule_group_closed_df,schedule_group_holiday_df],axis=1)

            elif sched_group['holidaySchedules'] != []: 
                schedule_group_df = pd.json_normalize(sched_group).explode('openSchedules').drop(['id','holidaySchedules'],axis=1)

                schedule_group_df['Duplicated'] = schedule_group_df.duplicated(subset=['name','division', 'timeZone'],keep="first")
                schedule_group_df.loc[schedule_group_df["Duplicated"] == True, ['name','division', 'timeZone']] = NaN
                schedule_group_df.drop("Duplicated",axis=1, inplace=True)

                schedule_group_holiday_df = pd.json_normalize(sched_group,record_path='holidaySchedules')
                schedule_group_holiday_df.columns = ['holidaySchedules']

                schedule_group_df.reset_index(inplace=True, drop=True)
                schedule_group_df = pd.concat([schedule_group_df,schedule_group_holiday_df],axis=1)

            else:
                schedule_group_df = pd.json_normalize(sched_group).explode('openSchedules').drop(['id'],axis=1)

                schedule_group_df['Duplicated'] = schedule_group_df.duplicated(subset=['name','division', 'timeZone'],keep="first")
                schedule_group_df.loc[schedule_group_df["Duplicated"] == True, ['name','division', 'timeZone']] = NaN
                schedule_group_df.drop("Duplicated",axis=1, inplace=True)       
            
            schedule_group_len = len(schedule_group_df) + 2

            schedule_group_df.to_excel(writer, sheet_name="Schedules & Schedule Groups", index=False, startrow=schedules_schedgroup_tab)
            schedules_schedgroup_tab += schedule_group_len

        error_members = {'Error':'*No Users Associated to the Clinic Location*'}
        if clinic['clinicMembers'] != []:
            clinic_member_df = pd.json_normalize(clinic,'clinicMembers').drop('id',axis=1)
        else:
            clinic_member_df = pd.json_normalize(error_members)

        clinic_member_df.to_excel(writer, sheet_name="Clinic Members", index=False)   

        writer.save()



    
        '''format_english = workbook.add_format({'bg_color':'#d1f3fa'})
        format_spanish = workbook.add_format({'bg_color':'#dcefdd'})
        format_recorded = workbook.add_format({'bg_color':'#E8E8E8'})
        format_not_recorded = workbook.add_format({'bold': True, 'font_color': '#ff3333'})
        
        worksheet.conditional_format(f"A2:B{rows}",{'type': 'formula', 'criteria': '=$B2="English"', 'format': format_english})
        worksheet.conditional_format(f"A2:B{rows}",{'type': 'formula', 'criteria': '=$B2="Spanish"', 'format': format_spanish})
        worksheet.conditional_format(f"C2:D{rows}",{'type': 'formula', 'criteria': '=$C2="Recorded"', 'format': format_recorded})
        worksheet.conditional_format(f"C2:D{rows}",{'type': 'formula', 'criteria': '=$C2="*Not Recorded*"', 'format': format_not_recorded})

        table_headers = [{'header': 'Prompt Name'}, {'header': 'Language'}, {'header': 'Status'}, {'header': 'Duration'}]
    
        worksheet.add_table(f"A1:D{rows}",{'style': 'Table Style Light 11', 'columns': table_headers})
        writer.save()'''
                


            


def main():
    #getting all base data    
    get_api_token()
    print("...Getting Site Info")
    get_sites()
    print("...Getting Location Info")
    get_locations()
    print("...Getting Group Info")
    get_groups()
    print("...Getting Emergency Group Info")
    get_emergency_groups()
    print("...Getting Queues Info")
    get_queues()
    print("...Getting DIDs")
    get_dids()
    print("...Getting Prompts")
    get_prompts()
    print("...Getting Schedules")
    get_schedules()
    print("...Getting Schedules Groups")
    get_schedule_groups()
    print("...Gathering Users Information and Memberships")    
    get_all_users()
    
    #looking through all base data for by name for each clinic
    search_for_clinic()
    print("...Searching through Info for Clinic Data") 

    #for each clinic get membership of base data and match names with ids
    print("...Finding all Clinic Associations")
    get_site_phones()
    get_queue_members()
    get_group_members()

    #getting location membership by all user locations. From location membership
    #creating another dict with user attributes to clinic dict.
    print("...Grouping Locations Memembership")
    location_membership()
    #getting name of objects to replace ids
    user_membership()
    schedule_names()
    
    #creating Dataframes for each sub-dict in clinic dict
    print("...All Finished Creating Excel files for each Clinic")
    create_excel()


if __name__ == '__main__':
    main()
    

