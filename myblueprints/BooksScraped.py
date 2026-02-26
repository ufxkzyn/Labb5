from flask import Blueprint, jsonify, render_template, request, Flask
import os  # Import the os module to cehck if json file exist or not
import requests  # Import the requests module to make HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup from bs4 to parse HTML
import json  # Import the json module to work with JSON data
import re
import datetime

BooksScraped = Blueprint('BooksScraped', __name__, template_folder='templates')

Full_book_list = './JsonData/Full_book_list' #. betyder leta specifikt här å sen gå in i jsondat

global currenttime  #might be stupid to put it as a global thing idk
currenttime = datetime.datetime.now().strftime("%Y-%m-%d") #used to get the current time, this is used to check when the json file was created and decide if we should scrape again or not.


@BooksScraped.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html'), 200


#### function for opening the json ####
@BooksScraped.route('/allbooks', methods=['GET', 'POST'])
def get_books():
    try:
        if os.path.exists(f'{Full_book_list}_{currenttime}.json'): #If the json file exsist we just open it
            print("found")
            with open(f'{Full_book_list}_{currenttime}.json', encoding='utf-8') as file_pointer_exsisting_found:
                all_books = json.load(file_pointer_exsisting_found)
                source = "local_json_file"

        else: #if it dosent exsist we make one
            print('inget hittat, skapar fil och folder')   
            if not os.path.exists('./JsonData'): #checks if the folder exsist, if not it makes one
                os.mkdir('./JsonData') #makes the folder if it dosent exsist

            all_books = scrape_books()
            source = 'live_web_scrape'
            if all_books:
                with open(f'{Full_book_list}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_new:
                    json.dump(all_books, file_pointer_new, ensure_ascii=False, indent=4)
            convert_price(all_books)  ###convert_price() and split_json() is kept in the else loop to prevent bugs
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
                #category_filename = f'./JsonData/{category_name}.json'
                with open(f'./JsonData/{category_name}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_category:
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
        return books

## Change the info of a book
@BooksScraped.route('/ChangeBooks', methods=['GET', 'POST'])
def change_books():
    try:
        picked_category = request.form.get('category')
        with open(f'{picked_category}_{currenttime}.json', 'r', encoding='utf-8') as file_pointer_changing:
            whats_changing = json.load(file_pointer_changing)

            Picked_book = request.form.get('title') 
            if Picked_book in whats_changing['books']:
                if 'title' in request.form and not "": ##the and not "" makes sure user isent inputting empty
                    updated_title = request.form.get('title')
                if 'booklink' in request.form and not "":
                    updated_link = request.form.get('booklink')
                if 'rating' in request.form and not "":
                    updated_rating = request.form.get('rating')
                if 'thumbnail' in request.form and not "":
                    updated_thumbnail = request.form.get('thumbnail')
                if 'gbpprice' in request.form and not "":
                    updated_gbpprice = request.form.get('gbpprice')
                if 'sekprice' in request.form and not "":
                    updated_sekprice = request.form.get('sekprice')

                updated_info_books = {             ## updates the info if its been changed, otherwise it keeps the same info
                    'title': updated_title if 'title' in request.form else whats_changing['books'][Picked_book]['title'],
                    'booklink': updated_link if 'booklink' in request.form else whats_changing['books'][Picked_book]['booklink'],
                    'rating': updated_rating if 'rating' in request.form else whats_changing['books'][Picked_book]['rating'],
                    'thumbnail': updated_thumbnail if 'thumbnail' in request.form else whats_changing['books'][Picked_book]['thumbnail'],
                    'gbpprice': updated_gbpprice if 'gbpprice' in request.form else whats_changing['books'][Picked_book]['gbpprice'],
                    'sekprice': updated_sekprice if 'sekprice' in request.form else whats_changing['books'][Picked_book]['sekprice']
                }
                whats_changing['books'][Picked_book] = updated_info_books

            with open(f'{picked_category}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_changing:
                json.dump(whats_changing, file_pointer_changing, ensure_ascii=False, indent=4)

        return (jsonify({"message": "Book updated successfully"}), 200,)
    except Exception as e:
        print(f'Error, cant change book{e}')

## change theinfo on a category
@BooksScraped.route('/ChangeCategory', methods=['POST', 'GET'])
def change_category():
    try:
        Picked_Category = request.form.get('category') 
        if Picked_Category:
            if 'category' in request.form and not "":
                updated_category = request.form.get('category')
            if 'categorylink' in request.form and not "":
                updated_link = request.form.get('categorylink')

            updated_info_categories = {
                'category': updated_category,
                'categorylink': updated_link}

            with open(f'{Picked_Category}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_changing:
                json.dump(updated_info_categories, file_pointer_changing, ensure_ascii=False, indent=4)

        return (jsonify({"message": "Category updated successfully"}), 200,)
    except Exception as e:
        print(f'Error, cant change category{e}')

#Deletes a book after picking under what category
@BooksScraped.route('/deletebook', methods=['GET', 'POST'])
def delete_book():
    try:
        picked_category_delete = request.form.get('category')
        picked_book_delete = request.form.get('title')
        with open(f'{picked_category_delete}_{currenttime}.json', 'r', encoding='utf-8') as file_pointer_deleting:
            book_to_delete = json.load(file_pointer_deleting)
            if picked_book_delete in book_to_delete['books']:
                book_to_delete['books'].pop(picked_book_delete)
                with open(f'{picked_category_delete}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_deleting:
                    json.dump(book_to_delete, file_pointer_deleting, ensure_ascii=False, indent=4)
            else:
                return (jsonify({"message": f"Book not found"}), 404,)
        return (jsonify({"message": f"Book {picked_book_delete} deleted successfully"}), 200,)
    except Exception as e:
        print(f'Error, cant delete book{e}')

## deletes a category 
@BooksScraped.route('/deletecategory', methods=['GET', 'POST'])
def delete_category():
    try:
        picked_category_delete = request.form.get('category')
        if os.path.exists(f'{picked_category_delete}_{currenttime}.json'):
            os.remove(f'{picked_category_delete}_{currenttime}.json')
            os.remove(f'{Full_book_list[picked_category_delete]}_{currenttime}.json')
            return (jsonify({"message": f"Category deleted successfully"}), 200,)
        else:
            return (jsonify({"message": f"Category not found"}), 404,)
    except Exception as e:
        print(f'Error, cant delete category{e}')

## adds a new book
@BooksScraped.route('/addbooks', methods=['GET', 'POST'])
def add_book():
    try:
        picked_book_add = request.form.get('title')
        picked_category_add = request.form.get('category')

        with open(f'{picked_category_add}_{currenttime}.json', 'r', encoding='utf-8') as file_pointer_adding:
            book_to_add = json.load(file_pointer_adding)
            if picked_book_add not in book_to_add['books']:
                new_book = {
                    'title': request.form.get('title'),
                    'booklink': request.form.get('booklink'),
                    'rating': request.form.get('rating'),
                    'thumbnail': request.form.get('thumbnail'),
                    'gbpprice': request.form.get('gbpprice'),
                    'sekprice': request.form.get('sekprice')
                }

                book_to_add['books'][picked_book_add].append(new_book) 

                with open(f'{picked_category_add}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_adding:
                    json.dump(book_to_add, file_pointer_adding, ensure_ascii=False, indent=4)

                return (jsonify({"message": f"Book {picked_book_add} added successfully"}), 200,)
            else:
                return (jsonify({"message": f"Book already exists"}), 400,)
    except Exception as e:
        print(f'Error, cant add book{e}')

#adds a nwe category
@BooksScraped.route('/addcategory', methods=['GET', 'POST'])
def add_category():
    try:
        picked_category_add = request.form.get('category')
        with open(f'{picked_category_add}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_adding:
            old_categorys = json.load(file_pointer_adding)

            if picked_category_add not in old_categorys:
                new_category = {
                    'category': request.form.get('category'),
                    'categorylink': request.form.get('categorylink'),
                    'books': {}
                }
                old_categorys.append(new_category)
                with open(f'{picked_category_add}_{currenttime}.json', 'w', encoding='utf-8') as file_pointer_adding:
                    json.dump(old_categorys, file_pointer_adding, ensure_ascii=False, indent=4)

                return (jsonify({"message": f"Category {picked_category_add} added successfully"}), 200,)
            else:
                return (jsonify({"message": f"Category already exists"}), 400,)
    except Exception as e:
        print(f'Error, cant add category{e}')

# check when the json was last updated
@BooksScraped.route('/Lastupdate', methods=['GET', 'POST'])
def last_update():
    try:
        for json_file in os.listdir('./JsonData'):           
            if f"{json_file}" != f"{json_file.split('_')[0]}_{currenttime}.json": #checks if the file is up to date, if not it updates it
                print(f"File {json_file} is old, updating now")
                with open(f'Full_book_list_{currenttime}.json', 'r', encoding='utf-8') as f:
                    found_update_link = json.load(f)['categorylink'] #finds the link to the category in the old json file, so we can scrape it again and update it

                
                os.remove(f"./JsonData/{json_file}") #removes the old json file
            
                with open(f'./JsonData/{json_file}', 'w', encoding='utf-8') as file_pointer_new:
                    json.dump(books_in_category(found_update_link), file_pointer_new, ensure_ascii=False, indent=4)

                return (jsonify({"message": f"File {json_file} is old, updating now"}), 200, json_file)
        return (jsonify({"message": f"All files are up to date"}), 200,)
    except Exception as e:
        print(f'Error, cant check last update: {type(e).__name__}: {e}')

#### not used ###
@BooksScraped.route('/Firstbuttons', methods=['GET', 'POST'])
def buttonchoice():
    try:
        action = request.form.get('action')
        if action == "Category":
            return (render_template('index.html', action=action), 200)
        if action == "Books":
            return (render_template('index.html', action=action), 200)
        if action == "update":
            file = last_update()
            return (render_template('index.html', action=action, updated_categories=file), 200)
    except Exception as e:
        print(f'Error, cant choose button{e}')


