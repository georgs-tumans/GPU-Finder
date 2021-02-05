import scrapy
import smtplib, ssl
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yaml
from pathlib import Path
from datetime import date
from datetime import datetime
import json
import pprint

#ToDO
# 1. Add other websites


class GpuFinder(scrapy.Spider):


    with open(Path(__file__).parent / "../config.yaml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    
    name = "gpus"       #spider name
    product = cfg['product']    #product we will be looking for
    port = cfg['port']  # For SSL
    password = cfg['password']
    smtp_server = cfg['smtp_server']
    sender_email = cfg['sender_email']
    receiver_email = cfg['receiver_email']

#########################################  Utilieties #######################################################
    def SendEmail(self, msgText, type=0):   #type=0 - informācija par atrastu preci/type=1 - info par kļūdām
    
        message = MIMEMultipart("alternative")  
        if type==0:  
            message["Subject"] = "Prece ir atrasta"
        else:
            message["Subject"] = "Notikusi kļūda"
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

    def log(self, content, newRun=0): 
        todayDate=str(date.today().strftime("%Y.%m.%d"))
        currentTime=str(datetime.now().strftime("%H:%M:%S"))
        with open("GPUfinder/logs/" + todayDate + "-log.txt", "a", encoding="utf-8") as fout:
            if newRun==1:
                fout.write("\n\n")
            fout.write(currentTime +"  " + content + "\n")
        


    ######################################## Crawler code #####################################################
    
    #sākuma punkts, norādītie urli tiks apmeklēti, katram izpildot 'parse' f-ju
    def start_requests(self):
        self.log("Script start", 1)
        urls = [
            'https://www.rdveikals.lv/search/lv/word/rx+5700/page/1/filters/437_0_0/',
            "https://www.rdveikals.lv/search/lv/word/rx+5600/page/1/",
            #test in  stock-> "https://www.rdveikals.lv/search/lv/word/580/page/1/",
            'https://sb.searchnode.net/v1/query/docs?query_key=qJCQ7AEn9cNmcFozKKFfSJVXf90mtDD2&search_query=rx%205700&sort.0=-inStock&sort.1=-score&offset=0&limit=48&facets.0=attr_*',
            "https://sb.searchnode.net/v1/query/docs?query_key=qJCQ7AEn9cNmcFozKKFfSJVXf90mtDD2&search_query=rx%205600&sort.0=-inStock&sort.1=-score&offset=0&limit=48&facets.0=attr_*",
            #->test in stock "https://sb.searchnode.net/v1/query/docs?query_key=qJCQ7AEn9cNmcFozKKFfSJVXf90mtDD2&search_query=rx%20580&sort.0=-inStock&sort.1=-score&offset=0&limit=48&facets.0=attr_*"
            #->error case "https://sb.searchnode.net/v1/query/docs?query_key=qJCQ7AEn9cNmcFozKKFfSJVXf90mtDD2&search_query=rx%205700&sort.0=-inStock&sort.1=-score&offset=0&limit=77&facets.0=attr_*"
            "https://www.dateks.lv/meklet?q=rx%205700",
            "https://www.dateks.lv/meklet?q=rx%205600",
            "https://220.lv/lv/datortehnika/datoru-komponentes/videokartes-gpu"
            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)    

    #katram norādītajam urlim izpildīsies šī f-ja
    def parse(self, response):
        if "rdveikals" in str(response.url):
            self.processRDVeikals(response)
        elif "searchnode" in str(response.url):
            self.process1A(response)
        elif "dateks" in str(response.url):
            self.processDateks(response)
        elif "220" in str(response.url):
            self.process220(response)
        return
        
    
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
        msgText="Veikalā RD Electronics tika atrastas sekojošas preces:\n\n"

        for el in resListElements:
            try:
               prodInfo=str(el.find('div', 'product__info').find('a').text).strip()
               for prod in self.product:
                #meklēšanas rezultāti satur vajadzīgo preci  - izvelkam saiti, cenu un sūtam epastu ar info:
                if prod in prodInfo:
                    print("Found the product!")
                    found=True
                    link=str(el.find('div', 'product__info').find('a')['href']).strip()
                    link="https://www.rdveikals.lv/"+link
                    price=str(el.find('div', 'product__info').find('p').text).strip()
                    msgText=msgText + prodInfo + "\nSaite: "+ link + "\nCena: " + price + "\n\n"
                    self.log("Found the product " + prodInfo + " for " + price + ". Available: " + link + ". Sending email..")
                   
               print(prodInfo)

            except Exception as e:
                self.log("Failed to process a search result: " + str(e))
                pass

        if found == False:
            self.log("Didn't find the product")
        else:
            self.SendEmail(msgText, 0)
       

    def process1A(self, response):
        #1A.lv gadījumā dati nāk ar json no atsevišķa url izsaukuma, nevis tiek iešūti html saturā
        self.log("Processing 1A")
        try:
            data = json.loads(response.body)
        except Exception as e:
            self.log("Failed to parse json: " + str(e))
            return

        if "error" in data:
            error=data["error"]["msg"]
            print("Invalid query: " + str(error))
            self.log("Request error: " + str(error) + ". Called URL: " + str(response.url))
            msgText="Kļūda, apstrādājot 1A.lv:\n\n" + str(error) + ".\n\nIzsauktais URL:\n" + str(response.url)
            self.SendEmail(msgText, 1)
            return
        results=data["docs"]
        found=False
        msgText="Veikalā 1A.lv tika atrastas sekojošas preces:\n\n"

        for r in results:
            try:
                title=r["title"]
                for prod in self.product:
                    #specifiska atlase, jo 1A pārdod cooling produktus konkrētajai videokartei, kas nav vajadzīgi
                    if prod in title and "water" not in title.lower() and "samos" not in title.lower() and r["inStock"] == True:
                        url=r["url"]
                        url="https://www.1a.lv"+url
                        price=r["priceDefault"]
                        print(title + " " + str(price) + " " + url)
                        self.log("Found the product " + title + " for " + str(price) + ". Available: " + url + ". Sending email..")
                        msgText=msgText + title + "\nSaite: "+ url + "\nCena: " + str(price) + "\n\n"   
                        found=True
                print(title)

            except Exception as e:
                self.log("Failed to process a search result: " + str(e))
                pass

        if found == False:
            self.log("Didn't find the product")
        else:
            self.SendEmail(msgText, 0)

        
    def processDateks(self, response):
        responseData=str(response.text)
        self.log("Processing Dateks")
        try:
            soup = BeautifulSoup(str(responseData), 'html.parser')
        except Exception as e:
            print("Error parsing the page")
            self.log("Error parsing the page: " + str(e))

        try:
            results = soup.find('div', 'page')
            resListElements = results.find_all('div', 'prod')
        except Exception as e:
            print("Failed to parse the search results")
            self.log("Failed to parse the search results" + str(e))

        
        found=False
        msgText="Veikalā Dateks tika atrastas sekojošas preces:\n\n"

        for el in resListElements:
            try:
                prodInfo=str(el.find('div', 'name').text).strip()
                link=str(el.find('div', 'top').find('a')['href']).strip()
                for prod in self.product:
                    if prod in prodInfo and "water" not in prodInfo.lower() and "ryzen" not in prodInfo.lower() and "coolers" not in link.lower():
                        print("Found " + prod)
                        found=True
                        link="https://www.dateks.lv"+link
                        price=str(el.find('div', 'mid').find('div', 'price').text).strip()
                        msgText=msgText + prodInfo + "\nSaite: "+ link + "\nCena: " + price + "\n\n"
                        self.log("Found the product " + prodInfo + " for " + price + ". Available: " + link + ". Sending email..")
                    
                print(prodInfo)

            except Exception as e:
                self.log("Failed to process a search result: " + str(e))
                pass

        if found == False:
            self.log("Didn't find the product")
        else:
            self.SendEmail(msgText, 0)

    def process220(self, response):
        responseData=str(response.text)
        self.log("Processing 220.lv")
        try:
            soup = BeautifulSoup(str(responseData), 'html.parser')
        except Exception as e:
            print("Error parsing the page")
            self.log("Error parsing the page: " + str(e))

        try:
            results = soup.find('div', {"id": "productListLoader"})
            resListElements = results.find_all('div', 'product-list-item')
        except Exception as e:
            print("Failed to parse the search results")
            self.log("Failed to parse the search results" + str(e))

        
        found=False
        msgText="Veikalā 220.lv tika atrastas sekojošas preces:\n\n"

        for el in resListElements:
            try:
                prodInfo=str(el.find('p', 'product-name').text).strip()
                available=el.find('span', 'label-soldout')
                for prod in self.product:
                    if prod in prodInfo and available == None:
                        print("Found " + prod)
                        found=True
                        link=str(el.find('p', 'product-name').find('a')['href']).strip()
                        price=str(el.find('div', 'product-price').find('span', 'price notranslate').text).strip()
                        msgText=msgText + prodInfo + "\nSaite: "+ link + "\nCena: " + price + "\n\n"
                        self.log("Found the product " + prodInfo + " for " + price + ". Available: " + link + ". Sending email..")
                    
                print(prodInfo)

            except Exception as e:
                self.log("Failed to process a search result: " + str(e))
                pass

        if found == False:
            self.log("Didn't find the product")
        else:
            self.SendEmail(msgText, 0)
