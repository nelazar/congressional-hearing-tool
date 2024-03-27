"""
Functions to consume the govdata.gov API
"""


import requests


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