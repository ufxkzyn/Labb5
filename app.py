from flask import Blueprint, jsonify, render_template, request, Flask
import datetime
import os  # Import the os module to cehck if json file exist or not
import requests  # Import the requests module to make HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup from bs4 to parse HTML
import json  # Import the json module to work with JSON data
import re




from myblueprints.BooksScraped import BooksScraped



app = Flask(__name__)
app.json.sort_keys = False ## added so we can decide order we print jsonify out, without this its alphabetical order

app.register_blueprint(BooksScraped, url_prefix='/') 



# Startar applikationen
if __name__ == "__main__": 
    # debug=True gör att servern startar om automatiskt när du ändrar i koden
    app.run(debug=True)
