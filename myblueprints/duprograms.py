from flask import Blueprint, jsonify, render_template, request, Flask
import os  # Import the os module to cehck if json file exist or not
import requests  # Import the requests module to make HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup from bs4 to parse HTML
import json  # Import the json module to work with JSON data
import re


duprograms = Blueprint('duprograms', __name__, template_folder='templates')

PROGRAM_CACHE_FILE = "program_cache.json"



@duprograms.route('/', methods=['GET'])
def index():
    return render_template('index.html')



@duprograms.route('/allprograms', methods=['GET', 'POST'])
def get_programs():
    if os.path.exists(PROGRAM_CACHE_FILE):
        print("found")
        with open(PROGRAM_CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            source = "local_json_file"
    
    else:
        print('inget hittat, skapar fil')
        data = scrape_du_programs()
        source = 'live_web_scrape'
        if data:
            with open(PROGRAM_CACHE_FILE,'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    return jsonify({
        "provider": "DU",
        "Source": source,
        "count": len(data),
        "program": data
    })

def scrape_du_programs():
    url = "https://www.du.se/sv/utbildning/program/"

    headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
    
    programs = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser') #skickar in i soup

        div_containers = soup.find_all('div', class_='panel-heading-title')  #letar efter () parametrarna

        for div in div_containers:
            linked_tags = div.find('a') #letar efter 'a'

            if linked_tags:
                title = linked_tags.get_text(strip=True) #letar efter tags, tar bort onödig text

                relative_link = linked_tags.get('href')

                full_link = f'https://www.du.se{relative_link}' if relative_link.startswith('/') else relative_link

            programs.append({
                'Programnamn': title,
                'Link': full_link
            })

    except Exception as e:

        print(f'gg fail{e}')
    return render_template('index.html', programs=programs, )
