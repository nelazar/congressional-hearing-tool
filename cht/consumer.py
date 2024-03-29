"""
Functions to consume the govdata.gov API
"""

import os

import requests

from cht import KEY_VAR, OUTPUT_PATH
from cht.customtypes import format_str
from cht.helper import congress_from_id
from cht.database import Database


# Makes a small API request to test if the given API key is valid
def test_key(key: str) -> bool:
    params = {
        'pageSize': 10,
        'congress': 117,
        'docClass': 'hhrg',
        'offsetMark': '*',
        'api_key': key
    }
    url = 'https://api.govinfo.gov/collections/CHRG/1997-01-01T00%3A00%3A00Z'

    response = requests.get(url, params)
    if response.status_code != 200:
        return False
    else:
        return True
    

# List the documents in a given Congress
def get_list(congress: int) -> list[str]:
    params = {
        'pageSize': 1000,
        'congress': congress,
        'docClass': 'hhrg',
        'offsetMark': '*',
        'api_key': os.environ[KEY_VAR]
    }
    url = 'https://api.govinfo.gov/collections/CHRG/1997-01-01T00%3A00%3A00Z'

    # Get list
    response = requests.get(url, params)
    if response.status_code != 200:
        raise SystemExit("API response error:", response.status_code, response.text)   
    ids: list[str] = []
    json = response.json()
    for package in json['packages']:
        ids.append(package['packageId'])

    # Account for pagination
    while json['nextPage'] is not None:
        url = f"{json['nextPage']}&api_key={os.environ[KEY_VAR]}"
        response = requests.get(url)
        if response.status_code != 200:
            raise SystemExit("API response error:", response.status_code, response.text)
        json = response.json()
        for package in json['packages']:
            ids.append(package['packageId'])
    
    return ids


# Downloads a set of documents given a list of IDs and a format
def download_documents(ids: list[str], format: format_str, quiet: bool=False) -> None:
    
    count = 0
    total = len(ids)
    failed = []

    for id in ids:

        count += 1
        if not quiet:
            print(f"Downloading {format} file {count}/{total}", end="\r")

        congress = congress_from_id(id)
        path = OUTPUT_PATH / format / str(congress) / f"{id}.{format}"

        with Database() as db:
            # Check if congress already downloaded from
            if congress not in db.get_files_congresses(format):
                congress_ids = get_list(congress)
                for congress_id in congress_ids:
                    db.add_file(congress_id, format, congress, None)

            # Check if already downloaded
            status = db.file_status(id, format)
            if status == 0: # Not downloaded
                db.update_path(id, format, path)
            elif status == 1: # Downloaded
                continue

        # Download file
        jacketid = f"{id[-5:-3]}-{id[-3:]}"
        match format:
            case 'txt':
                link_type = 'html'
            case 'xml':
                link_type = 'mods'
            case _:
                link_type = 'pdf'
        url = f"https://www.govinfo.gov/link/chrg/{congress}/{jacketid}?link-type={link_type}"
        response = requests.get(url, allow_redirects=True, stream=True)
        if response.status_code != 200:
            failed.append(id)
            continue
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) \
				AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 \
	    		Safari/537.36'}
        file_content = requests.get(response.url, headers=headers).content

        # Save file
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode='wb') as file:
            file.write(file_content)

    with Database() as db:
        for id in failed:
            db.delete_file(id, format)

    if not quiet:
        print()
        print("Completed downloads")
        if len(failed) > 0:
            print("Failed to download:")
            for id in failed:
                print(id)


# Parses all of the documents