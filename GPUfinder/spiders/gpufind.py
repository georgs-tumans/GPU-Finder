import scrapy
import smtplib, ssl
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yaml
from pathlib import Path
from datetime import date
from datetime import datetime

#ToDO
# 1. Add other websites


class GpuFinder(scrapy.Spider):

    with open(Path(__file__).parent / "../config.yaml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    
    name = "gpus"       #spider name
    product = str(cfg['product'])    #product we will be looking for
    port = cfg['port']  # For SSL
    password = cfg['password']
    smtp_server = cfg['smtp_server']
    sender_email = cfg['sender_email']
    receiver_email = cfg['receiver_email']

#########################################  Utilieties #######################################################
    def SendEmail(self, msgText):
    
        message = MIMEMultipart("alternative")    
        message["Subject"] = "Prece ir atrasta"
        message["From"] = self.sender_email
        message["To"] = self.receiver_email
        message.attach(MIMEText(msgText, "plain"))

        try:
            # Create a secure SSL context
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, self.receiver_email, message.as_string())
        except Exception as e:
            self.log("Failed to send an email: " + str(e))

    def log(self, content): 
        todayDate=str(date.today().strftime("%d.%m.%Y"))
        currentTime=str(datetime.now().strftime("%H:%M:%S"))
        with open("GPUfinder/logs/" + todayDate + "-log.txt", "a") as fout:
            fout.write(currentTime +"  " + content + "\n")
        


    ######################################## Crawler code #####################################################
    
    #sākuma punkts, norādītie urli tiks apmeklēti, katram izpildot 'parse' f-ju
    def start_requests(self):
        self.log("Script start")
        urls = [
            'https://www.rdveikals.lv/search/lv/word/rx+5700/page/1/filters/437_0_0/'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    #katram norādītajam urlim izpildīsies šī f-ja
    def parse(self, response):
        if "rdveikals" in str(response.url):
            self.processRDVeikals(response)
    
    def processRDVeikals(self, response):
        responseData=str(response.text)
        self.log("Processing RD Veikals")
        try:
            soup = BeautifulSoup(str(responseData), 'html.parser')
        except Exception as e:
            print("Error parsing the page")
            self.log("Error parsing the page: " + str(e))

        try:
            results = soup.find('ul', 'product-list product-list--grid product-list--with-overlay row row--pad block-top block-none-bottom')
            if results == None:
                notFound=soup.find('div',  'search__empty js-search-result-empty')
                if notFound!=None:
                    print("No results")
                    self.log("There are no search results")
                    return
                else:
                    print("Error processing missing content")
                    self.log("Error processing missing content")
                    return
        except Exception as e:
            print("Could not find the result 'ul'")
            self.log("Could not find the result 'ul': " + str(e))

        resListElements = results.find_all('li')
        found=False
        for el in resListElements:
            try:
               prodInfo=str(el.find('div', 'product__info').find('a').text).strip()
               #meklēšanas rezultāti satur vajadzīgo preci  - izvelkam saiti, cenu un sūtam epastu ar info:
               if self.product in prodInfo:
                   print("Found the product!")
                   found=True
                   link=str(el.find('div', 'product__info').find('a')['href']).strip()
                   link="https://www.rdveikals.lv/"+link
                   price=str(el.find('div', 'product__info').find('p').text).strip()
                   msgText="Veikalā RD Electronics tika atrasta meklētā prece.\nSaite: "+ link + "\nCena: " + price
                   self.log("Found the product " + self.product + " for " + price + ". Available: " + link + ". Sending email..")
                   self.SendEmail(msgText)
               print(prodInfo)

            except Exception as e:
                self.log("Failed to process a search result: " + str(e))
                pass
        if found == False:
            self.log("Didn't find the product")
        self.log("Script end\n")



