from urllib import response

from flask import Blueprint, jsonify, render_template, request, Flask
import os  # Import the os module to cehck if json file exist or not
import requests  # Import the requests module to make HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup from bs4 to parse HTML
import json  # Import the json module to work with JSON data
import re
import datetime

BooksScraped = Blueprint('BooksScraped', __name__, template_folder='templates')

Books_scraped_file = "books_cache.json"
Full_book_list = 'Full_book_list.json'


@BooksScraped.route('/', methods=['GET'])
def index():
    return render_template('index.html'), 200


#### function for opening the json ####
@BooksScraped.route('/allbooks', methods=['GET', 'POST'])
def get_books():
    if os.path.exists(Full_book_list): #If the json file exsist we just open it
        print("found")
        with open(Full_book_list, 'r', encoding='utf-8') as file_pointer_exsisting_found:
            data = json.load(file_pointer_exsisting_found)
            source = "local_json_file"
    else: #if it dosent exsist we make one
        print('inget hittat, skapar fil')   
        data = scrape_books()
        source = 'live_web_scrape'
        if data:
            with open(Full_book_list,'w', encoding='utf-8') as file_pointer_new:
                json.dump(data, file_pointer_new, ensure_ascii=False, indent=4)
    return jsonify(data)

#### function for getting all the categories ####
@BooksScraped.route('/allbooks', methods=['GET', 'POST'])
def scrape_books():
    url = "https://books.toscrape.com/" ## to get all the books, and pretending to be a browser.
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    category = []
    try:
        original_page = requests.get(url, headers=headers, timeout=10)
        original_soup = BeautifulSoup(original_page.text, 'html.parser')

        Find_Catagories = original_soup.find_all('div', class_='side_categories') #takes all the categories
        Find_Catagories = Find_Catagories[0].find_all('a') #finds the 'a' thats infront of the href 

        if Find_Catagories: #if the a infront is found we loop through 
            for item in Find_Catagories[1:]: #we chooice to start from 1 otherwise we first index the whole site ( might have been done once or twice))) 
                category_name = item.get_text(strip=True)
                category_link = f"https://books.toscrape.com/{item['href']}"
                category.append({
                    'category': category_name,
                    'link': category_link,
                    'books': books_in_category(category_link)
                    })
        return category
    except Exception as e:
        print(f'Error, cant scrape{e}')

####function for getting all the books in a category ####
def books_in_category(category_link):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    books = []
    try:
        category_page = requests.get(category_link, headers=headers, timeout=10)
        category_soup = BeautifulSoup(category_page.text, 'html.parser')
        while True:
            print(f"Going to next page: {category_link}")
            find_all_books = category_soup.find_all('ol', class_="row") #where the books are

            if not find_all_books:
                break
            find_each_book = find_all_books[0].find_all('article', class_="product_pod")  ## How all books are found

            if find_each_book:
                for book in find_each_book:
                    book_link = f"https://books.toscrape.com/catalogue/{book.find('h3').find('a')['href']}" #this tells us to go to h3, find 'a' then take the link
                    book_title = book.find('h3').find('a')['title'] #this tells us to go to h3, find 'a' then take the title
                    book_thumnail = book.find('div', class_='image_container').find('img')['src'] #this tells us to go to div, find image_container, then find img and take the src
                    book_price = book.find('p', class_='price_color').get_text().split('£') #this tells us to go to p, find price then remove the £ sign, still need to convert to sek 
                    books.append({
                        'title': book_title,
                        'link': book_link,
                        'thumbnail': book_thumnail,
                        'price': book_price[1]
                    })
            next_page = category_soup.find('li', class_='next') #used to find the next button
            if next_page:
                next_page_link = next_page.find('a')['href'] # used to get the link to the next page
                current_page = category_link.rsplit('/', 1)[0]    #https://www.geeksforgeeks.org/python/python-string-rsplit-method/
                category_link = f"{current_page}/{next_page_link}" #ads the /page-x.html to the current link, so we can go to the next page
                category_page = requests.get(category_link, headers=headers, timeout=10) ## we redo the thing from begining of try to get a new page
                category_soup = BeautifulSoup(category_page.text, 'html.parser')
            else:
                break
        return books
    except Exception as e:
        print(f'Error, cant scrape{e}')    


#### not used ###
@BooksScraped.route('/', methods=['POST'])
def buttonchoice():
    button_picked = request.form.get('show_all')  # Get the value of the button that was clicked
    if button_picked == 'show_all':
        buttonchoice == 'show_all_TRUE'
        return render_template('index.html', buttonchoice='show_all_TRUE')