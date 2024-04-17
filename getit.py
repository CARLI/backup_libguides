import json
import requests
import time
import os
from bs4 import BeautifulSoup as BSHTML
from urllib.parse import urlparse
from dotenv import load_dotenv
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--ids", help="Guide IDs", required=False)
args = parser.parse_args()
ids = args.ids

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET=os.getenv('CLIENT_SECRET')
CONTENT_URL=os.getenv('CONTENT_URL')

# We want to make certain to use HTTP keep-alive!!!
requests_session = requests.Session()


try:
  response = requests_session.post('https://lgapi-us.libapps.com/1.2/oauth/token',
    headers={
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    data={
     'client_id': CLIENT_ID,
     'client_secret': CLIENT_SECRET,
     'grant_type': 'client_credentials',
    }
  )
  ACCESS_TOKEN=response.json()['access_token']


  url = 'https://lgapi-us.libapps.com/1.2/guides'
  if (ids is not None):
    url += '/' + ids

  response = requests_session.get(url,
    headers={
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + ACCESS_TOKEN,
    },
    params={
      'expand': 'owner,subjects,pages,pages.boxes',
      #'expand': 'owner,group',
    }
  )
  for guide in response.json():
    print(json.dumps(guide, indent=4))
    print()

except Exception as err:
  print(err)
  exit(1)



