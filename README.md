# backup_libguides

## setup 
* Create virtual environment (venv)

python -m venv venv

* activate venv

source venv/bin/activate

* install libraries

pip3 install requests bs4 python-dotenv 

* configure .env file

cp dot_env .env

<pre>CLIENT_ID='123'
CLIENT_SECRET='somesecret'
CONTENT_URL='https://carli.libguides.com/ld.php?content_id='</pre>

## run script
python3 lg_backup.py
  
