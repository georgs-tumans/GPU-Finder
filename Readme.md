## Running: 

Execute cmd command in project directory - `scrapy crawl gpus`

Can also be run via the `runscraper.bat` file in project root folder

## Using:

To make the script search for additional products, add their name (search keyword) to the `product` list in the configuration file and the appropriate search url to the crawling url list (inside the `GPUfinder\GPUfinder\spiders\gpufind.py`)

**Important** - the bot expects the following parameters within `GPUfinder/config.yaml`:

* product: ["..", ".."]  - a list of products to look for. Ex: ["6700", "3070"]
* sender_email: ""  - the bot email account address that notifications will be sent from
* receiver_email: "" - the user email for receiving notifications
* port: 000 - the port number for connecting to the bot email account
* password: "" -  the bot email account password
* smtp_server: "" - the bot email account smtp server
* max_price: {} - a dictionary of max prices for **all** products from the first parameter. Example: {"6700" : 800, "3070":900}. Product names **must** be exactly the same as in the first parameter (product list). This is used to determine whether an email should be sent upon finding a product - emails are sent whenever the found product price is less or equeal to the one provided here.

## Developing

For site selector testing use scrapy shell. To use, go to project folder and run cmd: `scrapy shell "http://some_Url"`

## Dependencies:

To use the project, following modules have to be installed through pip:
* https://docs.scrapy.org/en/latest/index.html
* https://pyyaml.org/
* https://www.crummy.com/software/BeautifulSoup/

## Supported stores:
* https://www.1a.lv/
* https://www.rdveikals.lv/
* https://www.dateks.lv/
* https://220.lv/lv/
* https://m79.lv/
* https://oreol.eu/
* https://www.balticdata.lv/lv/
* https://www.elkor.lv/
