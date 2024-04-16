import json
import requests
import time
import os
from bs4 import BeautifulSoup as BSHTML
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET=os.getenv('CLIENT_SECRET')
CONTENT_URL=os.getenv('CONTENT_URL')

# We want to make certain to use HTTP keep-alive!!!
requests_session = requests.Session()

before = time.time()

def slurp_images(parent_dir, page):
  soup = BSHTML(page, features="html.parser")
  images = soup.findAll('img')

  for image in images:
    image_url = urlparse(image['src'])
    if not image_url.scheme:
      url_str = 'https:' + image_url.geturl()
    else:
      url_str = image_url.geturl()
    print("\t\t" + 'downloading image:', url_str)

    image_dir = parent_dir + '/images/' + image_url.hostname + '/' + os.path.dirname(image_url.path)
    if not os.path.exists(image_dir):
      os.makedirs(image_dir)
    image_file_name = image_dir + '/' + os.path.basename(image_url.path).split('/')[-1]
    html_response = requests_session.get(url_str)
    with open(image_file_name, "wb") as image_document:
      image_document.write(html_response.content)

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


  response = requests_session.get('https://lgapi-us.libapps.com/1.2/guides',
    headers={
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + ACCESS_TOKEN,
    },
    params={
      'expand': 'owner,subjects,pages,pages.boxes'
    }
  )
  for guide in response.json():
    ###print(guide)
    ###print('url', guide['url'])
    ###print('status', guide['status'])
    ###print('created', guide['created'])
    ###print('updated', guide['updated'])
    ###print()
    guide_dir = f"./data/guide/{guide['id']}/{guide['updated']}"
    if not os.path.exists(guide_dir):
      os.makedirs(guide_dir)
    with open(f"{guide_dir}/guide.json", "w") as guide_json:
      guide_json.write(json.dumps(guide))
    # only published (status == 1) pages are accessible
    if guide['status'] == 1:
      guide_filename = f"{guide_dir}/guide.html"
      if not os.path.exists(guide_filename):
        html_response = requests_session.get(guide['url'])
        with open(guide_filename, "w") as guide_html:
          print('downloading guide:', guide_filename)
          guide_html.write(html_response.text)
          slurp_images(guide_dir, html_response.text)
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
            slurp_images(page_dir, html_response.text)
      # download "Document / File" (type_id=4) assets within this guide
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
          ###print(asset)
          ###print('url', asset['url']) 
          ###print('created', asset['created'])
          ###print('updated', asset['updated'])
          ###print()
          asset_dir = f"{guide_dir}/asset/{asset['id']}/{asset['updated']}"
          if not os.path.exists(asset_dir):
            os.makedirs(asset_dir)
          asset_filename = f"{asset_dir}/asset.json"
          if not os.path.exists(asset_filename):
            print("\t\t" + 'downloading asset:', asset_filename)
            with open(f"{asset_filename}", "w") as asset_json:
              asset_json.write(json.dumps(asset))
            asset_doc_filename = f"{asset_dir}/{asset['meta']['file_name']}"
            if not os.path.exists(asset_doc_filename):
              html_response = requests_session.get(f"{CONTENT_URL}{asset['id']}")
              with open(asset_doc_filename, "wb") as asset_document:
                print("\t\t\t" + 'downloading asset file:', asset_doc_filename)
                asset_document.write(html_response.content)

  # list all assets separately
  response = requests_session.get('https://lgapi-us.libapps.com/1.2/assets',
    headers={
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + ACCESS_TOKEN,
    },
    params={
      'expand': 'subjects,icons,friendly_url'
    }
  )
  for asset in response.json():
    ###print(asset)
    ###print('url', asset['url']) 
    ###print('created', asset['created'])
    ###print('updated', asset['updated'])
    ###print()
    asset_dir = f"./data/asset/{asset['id']}/{asset['updated']}"
    if not os.path.exists(asset_dir):
      os.makedirs(asset_dir)
    asset_filename = f"{asset_dir}/asset.json"
    if not os.path.exists(asset_filename):
      with open(f"{asset_filename}", "w") as asset_json:
        print('downloading asset:', asset_filename)
        asset_json.write(json.dumps(asset))
      if asset['type_id'] == 4:
        asset_doc_filename = f"{asset_dir}/{asset['meta']['file_name']}"
        if not os.path.exists(asset_doc_filename):
          html_response = requests_session.get(f"{CONTENT_URL}{asset['id']}")
          with open(asset_doc_filename, "wb") as asset_document:
            print("\t" + 'downloading asset file:', asset_doc_filename)
            asset_document.write(html_response.content)

  print(f"Operation took {time.time() - before} seconds")

except Exception as err:
  print(err)
  exit(1)



