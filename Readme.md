## Running: 

Execute cmd command in project directory - `scrapy crawl gpus`

Can also be run via the `runscraper.bat` file in project root folder

## Using:

To make the script search for additional products, add their name (search keyword) in the config file and the appropriate search url to the crawling url list

**Important** - programm expects a python dictionary ('max_price') of product names and their max price. Example: {'3060':700, '5700':600}. Product name **must** be identical to those provided in product list ('product')

## Developing

For site selector testing use scrapy shell. To use, go to project folder and run cmd: `scrapy shell "http://some_Url"`

## Dependencies:

To use the project, following modules have to be installed through pip:
* https://docs.scrapy.org/en/latest/index.html
* https://pyyaml.org/
* https://www.crummy.com/software/BeautifulSoup/
