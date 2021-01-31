import scrapy
import smtplib, ssl
from bs4 import BeautifulSoup

#ToDO
# 1. Add logging to file
# 2. Put parameters into a yaml config file
# 3. Add other websites
# 4. Tune email content


class GpuFinder(scrapy.Spider):
    name = "gpus"
    gpu = "5700"


    def SendEmail(self):
        port = 465  # For SSL
        password = input("Type your password and press enter: ")
        smtp_server = "smtp.gmail.com"
        sender_email = "gpufindermail@gmail.com"  # Enter your address
        receiver_email = "georgs12@gmail.com"  # Enter receiver address
        message = "A product has been found!"

        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

    def start_requests(self):
        urls = [
            'https://www.rdveikals.lv/search/lv/word/rx+5700/page/1/filters/417_0_0/'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        
        
        responseData=str(response.text)
        try:
            soup = BeautifulSoup(str(responseData), 'html.parser')
        except:
            print("Error parsing the page")

        try:
            results = soup.find('ul', 'product-list product-list--grid product-list--with-overlay row row--pad block-top block-none-bottom')
            if results == None:
                notFound=soup.find('div',  'search__empty js-search-result-empty')
                if notFound!=None:
                    print("No results")
                    return
                else:
                    print("Error processing missing content")
                    return
        except:
            print("Could not find the result 'ul'")

        resListElements = results.find_all('li')
        for el in resListElements:
            try:
               prodInfo=str(el.find('div', 'product__info').find('a').text).strip()
               if self.gpu in prodInfo:
                   print("Found a card!")
                   self.SendEmail()
               print(prodInfo)

            except:
                pass


