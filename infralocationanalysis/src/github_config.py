import base64
import json
from pathlib import Path

import requests
import os

# Replace with your own GitHub username and personal access token
USERNAME = 'xxx'
TOKEN = 'xxx'

# Replace with the owner and repository name for the repository you want to upload to
REPO_OWNER = 'xxx'
REPO_NAME = 'xxx


def git_upload_file(FILE_NAME, FILE_PATH):
    # Authenticate with the GitHub API using the personal access token
    headers = {'Authorization': f'token {TOKEN}'}

    # Create a new repository file
    file_url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_NAME}'
    file_content = open(FILE_PATH, 'rb').read()
    # data = {
    #     'message': f'Add {FILE_NAME}',
    #     'content': base64.b64encode(file_content).decode('utf-8')
    # }
    try:
        # Check if the file exists in the repository
        response = requests.get(file_url, headers=headers)
        if response.status_code == 200:
            # File exists, update the file content
            file_info = json.loads(response.content)
            data = {
                'message': f'Update {FILE_NAME}',
                'content': base64.b64encode(file_content).decode('utf-8'),
                'sha': file_info['sha']
            }
            response = requests.put(file_url, headers=headers, data=json.dumps(data))
            print(response.json())
        else:
            # File does not exist, create the file with the new content
            data = {
                'message': f'Add {FILE_NAME}',
                'content': base64.b64encode(file_content).decode('utf-8'),
            }
            response = requests.put(file_url, headers=headers, data=json.dumps(data))
            print(response.json())

        response = requests.put(file_url, headers=headers, json=data)
    except Exception as e:
        print("upload failed.")
        return


def git_download_file(FILE_NAME, FILE_OUTPUT_PATH):
    # Construct the URL to download the file from
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/'+FILE_NAME

    # Add authorization header to the request
    headers = {'Authorization': f'token {TOKEN}',
               'Accept': 'application/vnd.github.full+json',
               }

    # Send the request to download the file
    response = requests.get(url, headers=headers, stream=True)

    # Check if the request was successful
    if response.status_code == requests.codes.ok:
        # Write the decoded content to a file
        data = json.loads(response.content)
        file_content = requests.get(data['download_url']).content
        with open(FILE_OUTPUT_PATH, 'wb') as f:
            f.write(file_content)
        print('File downloaded successfully!')
    else:
        print('Failed to download file:', response.json)


def git_append_file(FILE_NAME):
    # Construct the URL to download the file from
    res = {}
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/'+FILE_NAME

    # Add authorization header to the request
    headers = {'Authorization': f'token {TOKEN}',
               'Accept': 'application/vnd.github.full+json',
               }

    # Send the request to download the file
    response = requests.get(url, headers=headers, stream=True)

    # Check if the request was successful
    if response.status_code == requests.codes.ok:
        # Write the decoded content to a file
        data = json.loads(response.content)
        file_content = requests.get(data['download_url']).content
        res = json.loads(file_content)
        print('File appended successfully!')
    else:
        print('Failed to append file:', response.json)

    return res


def combine_file():
    countryList = []
    textPath = f"{Path(__file__).parent.parent}/data/countryList.txt"
    with open(textPath, "r") as f:
        for country in f:
            countryList.append(str(country)[:-1])
    if not os.path.exists("../downloads"):
        os.mkdir("../downloads")
    data_map = {}
    DNS_FILE_OUTPUT_PATH = '../downloads/cdnResults.json'
    for country in countryList:
        DL_DNS_FILE_NAME = 'cdn/cdn_centralization_'+country+'.json'
        res = git_append_file(DL_DNS_FILE_NAME)
        if len(res) == 0:
            print("Failed to append file in country: ", country)
        else:
            data_map[country] = res[country]

    with open(DNS_FILE_OUTPUT_PATH, 'w') as f:
        json.dump(data_map, f)

if __name__ == "__main__":
    # Replace with the file name and path of the file you want to upload
    # FILE_NAME = 'dns/googleTop1000SitesCountries.json'
    # FILE_PATH = '../data/googleTop1000SitesCountries.json'
    # # git_upload_file(FILE_NAME, FILE_PATH)
    # if not os.path.exists("../downloads"):
    #     os.mkdir("../downloads")
    # FILE_OUTPUT_PATH = 'results/resources/resources_CR.json'
    # DL_FILE_NAME = 'cdn/resources_CR.json'
    # git_download_file(DL_FILE_NAME, FILE_OUTPUT_PATH)

    combine_file()