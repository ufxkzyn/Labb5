from flask import Blueprint, jsonify, render_template, request, Flask
import os  # Import the os module to cehck if json file exist or not
import requests  # Import the requests module to make HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup from bs4 to parse HTML
import json  # Import the json module to work with JSON data
import re
import datetime

BooksScraped = Blueprint('BooksScraped', __name__, template_folder='templates')

Books_scraped_file = "books_cache.json"



@BooksScraped.route('/', methods=['GET'])
def index():
    return render_template('index.html')



@BooksScraped.route('/allprograms', methods=['GET', 'POST'])
def get_programs():
    if os.path.exists(Books_scraped_file):
        print("found")
        with open(Books_scraped_file, 'r', encoding='utf-8') as file_pointer_exsisting_found:
            data = json.load(file_pointer_exsisting_found)
            source = "local_json_file"
    
    else:
        print('inget hittat, skapar fil')   
        data = scrape_books()
        source = 'live_web_scrape'
        data.insert(0, {"timestamp": datetime.datetime.now().isoformat()})  # Lägg till tidsstämpel i början av listan

        if data:
            with open(Books_scraped_file,'w', encoding='utf-8') as file_pointer_new:
                json.dump(data, file_pointer_new, ensure_ascii=False, indent=4)
    return render_template('index.html', data=data, source=source, count=len(data))

def scrape_books():
    url = "https://books.toscrape.com/"

    headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
    Books = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser') #skickar in i soup

        
                                #mellanslag betyder att vi kollar i alla div efter nästa, medans > betyder att det måste vara en child
        li_container = soup.css.select('#default div div div aside div.side_categories > ul > li > ul > li') #genom att högerclicka där vi vill vara och välja "copy selector" så får vi sökvägen direkt där vi vill vara, så fkn ez
        soup.select('div.side_categories')
        
        for li in li_container:
            linked_tags = li.find('a') #letar efter 'a'
            
            if linked_tags: #om det finns 'a' så gör detta, annars hoppar den över
                title = linked_tags.get_text(strip=True) #letar efter tags, tar bort onödig text

                relative_link = linked_tags.get('href')

                full_link = f'https://books.toscrape.com/{relative_link}' #if relative_link.startswith('/') else relative_link

            Books.append({
                'Länk': full_link,
                'kategori': title,
            }) 
    except Exception as e:
        print(f'gg fail{e}')
    return (Books)
 

@BooksScraped.route('/', methods=['POST'])
def buttonchoice():
    button_picked = request.form.get('show_all')  # Get the value of the button that was clicked
    if button_picked == 'show_all':
        buttonchoice == 'show_all_TRUE'
        return render_template('index.html', buttonchoice='show_all_TRUE')