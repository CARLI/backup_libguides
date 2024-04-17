import json
import requests
import time
import os
from bs4 import BeautifulSoup as BSHTML
from urllib.parse import urlparse
from dotenv import load_dotenv
import argparse
import hashlib
from io import BytesIO

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

before = time.time()

# General-purpose solution that can process large files
def file_hash(file_contents):
  # https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
  sha256 = hashlib.sha256()
  while True:
    data = file_contents.read(65536) # arbitrary number to reduce RAM usage
    if not data:
      break
    sha256.update(data)
  return sha256.hexdigest()

def slurp_images(parent_dir, date_str, page):
  soup = BSHTML(page, features="html.parser")
  images = soup.findAll('img')

  for image in images:
    image_url = urlparse(image['src'])
    if not image_url.scheme:
      url_str = 'https:' + image_url.geturl()
    else:
      url_str = image_url.geturl()
    print("\t\t" + 'downloading image:', url_str)

    image_dir = parent_dir + '/image/' + image_url.hostname + '/' + image_url.path
    image_file_name = os.path.basename(image_url.path).split('/')[-1]
    if not os.path.exists(image_dir):
      os.makedirs(image_dir)

    html_response = requests_session.get(url_str)
    file_like = BytesIO(html_response.content)
    hash_value = file_hash(file_like)

    hash_value_dir = image_dir + '/' + hash_value 
    if not os.path.exists(hash_value_dir):
      os.makedirs(hash_value_dir)
      print("\t\t\t" + 'saving new image: ' + image_file_name + ' (hash: ' + hash_value + ')')
      with open(hash_value_dir + '/' + image_file_name, "wb") as image_document:
        image_document.write(html_response.content)
    else:
      print("\t\t\t" + 'not saving image since it hasn\'t changed: ' + image_file_name + ' (hash: ' + hash_value + ')')

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
      'expand': 'owner,subjects,pages,pages.boxes'
    }
  )
  for guide in response.json():
    guide_parent_dir = f"./data/guide/{guide['id']}"
    guide_dir = f"{guide_parent_dir}/{guide['updated']}"
    if not os.path.exists(guide_dir):
      os.makedirs(guide_dir)
    guide_json_filename = f"{guide_dir}/guide.json"
    if not os.path.exists(guide_json_filename):
      with open(f"{guide_json_filename}", "w") as guide_json:
        print('downloading guide:', guide_json_filename)
        guide_json.write(json.dumps(guide, indent=4))
    # only published (status=1) or private (status=2 )pages are accessible
    if guide['status'] == 1 or guide['status'] == 2:
      for page in guide['pages']:
        page_dir = f"{guide_dir}/page/{page['id']}/{page['updated']}"
        if not os.path.exists(page_dir):
          os.makedirs(page_dir)
        page_filename = f"{page_dir}/page.html"
        if not os.path.exists(page_filename):
          html_response = requests_session.get(page['url'])
          with open(page_filename, "w") as page_html:
            print("\t" + 'downloading page:', page_filename)
            page_html.write(html_response.text)
            slurp_images(guide_parent_dir, page['updated'], html_response.text)
      # download assets within this guide (similar to slurping images)
      asset_response = requests_session.get('https://lgapi-us.libapps.com/1.2/assets',
        headers={
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + ACCESS_TOKEN,
        },
        params={
          'guide_ids': guide['id'],
          'expand': 'subjects,icons,friendly_url'
        }
      )
      for asset in asset_response.json():
        if asset['type_id'] == 4:
          asset_doc_filename = asset['meta']['file_name']
          asset_dir = f"./data/guide/{guide['id']}/asset/{asset['id']}/{asset_doc_filename}"
          if not os.path.exists(asset_dir):
            os.makedirs(asset_dir)
          html_response = requests_session.get(f"{CONTENT_URL}{asset['id']}")
          file_like = BytesIO(html_response.content)
          hash_value = file_hash(file_like)
          hash_value_dir = asset_dir + '/' + hash_value 
          if not os.path.exists(hash_value_dir):
            os.makedirs(hash_value_dir)
            print("\t\t\t" + 'saving new asset file: ' + asset_doc_filename + ' (hash: ' + hash_value + ')')
            with open(hash_value_dir + '/' + asset_doc_filename, "wb") as asset_document:
              asset_document.write(html_response.content)
            asset_filename = f"{hash_value_dir}/{asset['updated']}.json"
            if not os.path.exists(asset_filename):
              print("\t\t" + 'saving asset object:', asset_filename)
              with open(f"{asset_filename}", "w") as asset_json:
                asset_json.write(json.dumps(asset, indent=4))

  print(f"Operation took {time.time() - before} seconds")

except Exception as err:
  print(err)
  exit(1)



