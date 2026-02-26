from flask import Blueprint, jsonify, render_template, request, Flask
import os  # Import the os module to cehck if json file exist or not
import requests  # Import the requests module to make HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup from bs4 to parse HTML
import json  # Import the json module to work with JSON data
import re
import datetime

BooksScraped = Blueprint('BooksScraped', __name__, template_folder='templates')

Full_book_list = './JsonData/Full_book_list' #. betyder leta specifikt här å sen gå in i jsondat

global currentime  #might be stupid to put it as a global thing idk
currenttime = datetime.datetime.now().strftime("%Y-%m-%d") #used to get the current time, this is used to check when the json file was created and decide if we should scrape again or not.


@BooksScraped.route('/', methods=['GET'])
def index():
    return render_template('index.html'), 200


#### function for opening the json ####
@BooksScraped.route('/allbooks', methods=['GET', 'POST'])
def get_books():
    try:
        if os.path.exists(f'{Full_book_list}_{currenttime}.json'): #If the json file exsist we just open it
            print("found")
            with open(f'{Full_book_list}_{currenttime}.json', encoding='utf-8') as file_pointer_exsisting_found:
                data = json.load(file_pointer_exsisting_found)
                source = "local_json_file"

        else: #if it dosent exsist we make one
            print('inget hittat, skapar fil och folder')   
            if not os.path.exists('./JsonData'): #checks if the folder exsist, if not it makes one
                os.mkdir('./JsonData') #makes the folder if it dosent exsist

            data = scrape_books()
            source = 'live_web_scrape'
            if data:
                with open(f'{Full_book_list}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_new:
                    json.dump(data, file_pointer_new, ensure_ascii=False, indent=4)
            convert_price(data)  ###convert_price() and split_json() is kept in the else loop to prevent bugs
            split_json()
        return (jsonify({"message": f"Books retrieved from {source}"}), 200)
    except Exception as e:
        print(f'Error, cant get books{e}')


###function for splitting up the whole json file into smaller json files based on category #
@BooksScraped.route('/splitjson', methods=['GET', 'POST'])
def split_json():
    try:
        with open(f'{Full_book_list}_{currenttime}.json', 'r', encoding='utf-8') as file_pointer_split:
            temporary_split = json.load(file_pointer_split)
            for category in temporary_split:
                category_name = category['category'] #takes all categories and saves them in the .json file with their respective name
                category_filename = f'./JsonData/{category_name}.json'
                with open(f'{category_filename}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_category:
                    json.dump(category, file_pointer_category, ensure_ascii=False, indent=4)  
            return (jsonify({"message": "JSON file split successfully"}), 200)
    except Exception as e:
        print(f'Error, cant split json{e}')


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
                    'categorylink': category_link,
                    'books': books_in_category(category_link)
                    })
        return category
    except Exception as e:
        print(f'Error, cant scrape{e}')


##function for converting ##
@BooksScraped.route('/convertprice', methods=['GET', 'POST'])
def convert_price(category):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    price_converted = []


    try:
        currency_soup = requests.get("https://www.x-rates.com/table/?from=GBP&amount=1", headers=headers, timeout=10) ### This site tried to avoid scraping so this might be unusable in the future
        currency_soup = BeautifulSoup(currency_soup.text, 'html.parser')
        find_price = currency_soup.find('div', class_="moduleContent").find('table', class_="tablesorter ratesTable")

        price_converted = get_conversion_rate(find_price) 

        with open(f'{Full_book_list}_{currenttime}.json', 'r', encoding='utf-8') as file_pointer_converting:
            file_currency_converter = json.load(file_pointer_converting)

            for categories in file_currency_converter:
                for book in categories['books']: 
                    gbp_price = book['gbpprice']
                    sek_price = round(float(gbp_price) * float(price_converted[0]['price']), 2) #gbpprice*conversion rate gives us the correct sek price, we also round it to 2 decimals for better presentation
                    category = {
                        'sekprice': sek_price,
                        'gbpprice': gbp_price
                    }
                    book.update(category)

            with open(f'{Full_book_list}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_converting:
                json.dump(file_currency_converter, file_pointer_converting, ensure_ascii=False, indent=4)
            return (jsonify({"message": "Prices converted successfully"}), 200)
    except Exception as e:
        print(f'Error, cant convert price{e}')


#### refactorized the conversion rate ####
@BooksScraped.route('/GBPtoSEK', methods=['GET', 'POST'])
def get_conversion_rate(find_price):
    price_converted = []
    for currency_finder in find_price.find_all('tr'): #looks for the swedish krona in 'tr', notice this function might requrie updates incase they change layout
        if 'Swedish Krona' in currency_finder.get_text():
            price_converted.append({
                'currency': 'SEK',
                'price': currency_finder.find_all('td')[1].get_text()
            })
    return price_converted


####function for getting all the books in a category ####
@BooksScraped.route('/BooksByCategory', methods=['GET', 'POST'])
def books_in_category(category_link):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    books = []
    try:
        category_page = requests.get(category_link, headers=headers, timeout=10)
        category_soup = BeautifulSoup(category_page.text, 'html.parser')
        #return f"<pre>{category_soup.prettify().replace('<', '&lt;').replace('>', '&gt;')}</pre>" #felsökning

        while True:
            print(f"Going to next page: {category_link}")
            find_all_books = category_soup.find_all('ol', class_="row") #where the books are

            if not find_all_books:
                break
            find_each_book = find_all_books[0].find_all('article', class_="product_pod")  ## How all books are found

            if find_each_book:
                for book in find_each_book:
                    book_link = f"https://books.toscrape.com/catalogue/{book.find('h3').find('a')['href']}" #this tells us to go to h3, find 'a' then take the link
                    book_link = re.sub(r'/../../..', '', book_link) #used to find the /../../.. and substitute it with nothing. (unsure for the reason why the link is so sus) 

                    book_thumnail = f"https://books.toscrape.com/{book.find('img')['src']}" #same as above but for the thumbnail
                    book_thumnail = re.sub(r'/../../../..', '', book_thumnail)

                    book_rating = book.find('p', class_='star-rating')['class'] #this tells us to go to p, find the star rating then take the second class which is the rating
                    book_title = book.find('h3').find('a')['title'] #this tells us to go to h3, find 'a' then take the title
                    book_price = book.find('p', class_='price_color').get_text().split('£') #this tells us to go to p, find price then remove the £ sign, still need to convert to sek 

                    books.append({
                        'title': book_title,
                        'booklink': book_link,
                        'rating': book_rating[1],
                        'thumbnail': book_thumnail,
                        'gbpprice': book_price[1],
                        'sekprice': 1 #placeholder value
                        
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