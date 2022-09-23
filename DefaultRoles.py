import PureCloudPlatformClientV2 as v2
import pandas as pd
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget, QApplication, QFileDialog,QGridLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import requests
import json
import os, sys

log = []
users = []
org_divisions = []
division_title = []


#GENESYS_CLOUD_CLIENT_ID_PE
#GENESYS_CLOUD_CLIENT_SECRET_PE

#environment variables for OAuth keys
GENESYS_CLOUD_CLIENT_ID = "01d781d2-b600-4b93-8a7d-e2778d0fcf56"
GENESYS_CLOUD_CLIENT_SECRET = "AobrjzsHjAABK67u2b4Mz-uSFRiQNAhqBDVqjAStGeY"


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

def get_divisions():
    all_divisions = []
    url = f"{api_url}authorization/divisions?"
    div_payload={}
    response = requests.request("GET", url, headers=headers, data=div_payload)
    all_divisions.append(json.loads(response.text))
    for div in all_divisions[0]['entities']:
        division_name = div.get('name')
        division_id = div.get('id')
        org_divisions.append({'id': division_id, 'name': division_name})



def get_all_users():
    user_list = []
    url = f"{api_url}users?pageSize=100"
    payload={}
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    user_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}users?pageSize=100&pageNumber={page_number}"
        payload={}
        response = requests.request("GET", page_url, headers=headers, data=payload)
        user_list.append(json.loads(response.text))

    for list in user_list:
        for user in list['entities']:
            id = user.get('id')
            name = user.get('name')

            users.append({'name': name, 'id': id})


def get_users_roles(id):
    url = f"{api_url}authorization/subjects/{id}"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    role_data = json.loads(response.text)
    user_roles = role_data['grants']
    role_ids = []
    for role in user_roles:
        role_ids.append(role['role'].get('id'))
    
    return role_ids
            
        

def set_user_roles(role_ids,user_id,div_id):
    new_grants = []
    for role_id in role_ids:
        new_grants.append({"roleId": role_id, "divisionId": div_id})

    url = f"{api_url}authorization/subjects/{user_id}/bulkreplace?subjectType=PC_USER"
    user_roles_payload = json.dumps({
        "grants": 
            new_grants
        })
    response = requests.request("POST", url, headers=headers, data=user_roles_payload)
    print(response.text)
    


class PeopleSetup(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()

        self.setStyleSheet("background-color: #778899;")
        self.setFixedSize(600,350)
    
        self.setWindowTitle("User Role to Division")

        self.import_button = QPushButton("Import Users CSV",self)
        self.import_button.setFont(QFont('Arial',12))
        self.import_button.setStyleSheet("padding: 5px; background-color: #DCDCDC; border-style: inset; border-color: #000000; border-width: 1px; border-radius: 2px;")
        self.import_button.clicked.connect(self.select_file)
        

        self.file_label = QLabel("", self)
        self.file_label.setFont(QFont('Arial',12))
        self.file_label.setVisible(False)

        self.layout = QGridLayout(self)
        self.layout.setSpacing(25)

        self.layout.addWidget(self.import_button,1,3,1,1,alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.file_label,1,2,1,4,alignment=Qt.AlignmentFlag.AlignCenter)


    def select_file(self):
        select_csv = QFileDialog.getOpenFileName(self, 'Import Your Users .csv File :', os.getcwd(),"(*.csv)")
        
        filename = select_csv
        if filename:
            self.fname = str(os.path.basename(filename[0]))
            self.file_label.setText(self.fname)

        self.file_label.setVisible(True)
        self.import_button.setVisible(False)

        users_csv = pd.read_csv(filename[0],usecols=['name','division'])
        
        names = users_csv['name']
        divisions = users_csv['division']

        user_list = []

        for name in names: 
            for user in users:
                if name == user['name']:
                    user_list.append(user)
                    
        for div_name in divisions:
            for div in org_divisions:
                if div_name == div['name']:
                    division_id = div.get('id')
                    division_title.append(div_name)
        
        self.change_user_roles(user_list, division_id)
        


    def change_user_roles(self, users_dict, div_id):
        for dict in users_dict:
            name = dict.get('name')
            id = dict.get('id')
            final_role_ids = get_users_roles(id)

            set_user_roles(final_role_ids,id,div_id)
            print(f"{name}'s roles and been set to the {division_title[0]} Division")

        self.close()


def main():
    get_api_token()
    get_all_users()
    get_divisions() 

    app = QApplication(sys.argv)

    window = PeopleSetup()

    window.show()

    app.exec()

if __name__ == '__main__':
    main()