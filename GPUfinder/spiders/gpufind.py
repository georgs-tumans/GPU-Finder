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
import re

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
    max_price = cfg['max_price']

#########################################  Utilieties #######################################################
    def SendEmail(self, msgText, type=0):   #type=0 - informācija par atrastu preci/type=1 - info par kļūdām
    
        message = MIMEMultipart("alternative")  
        if type==0:  
            message["Subject"] = "Prece ir atrasta"
        else:
            message["Subject"] = "Kļūda"
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

    def log(self, content, newRun=0, isError=0): 
        todayDate=str(date.today().strftime("%Y.%m.%d"))
        currentTime=str(datetime.now().strftime("%H:%M:%S"))
        with open("GPUfinder/logs/" + todayDate + "-log.txt", "a", encoding="utf-8") as fout:
            if newRun==1:
                fout.write("\n\n")
            fout.write(currentTime +"  " + content + "\n")
        if isError==1:
            with open("GPUfinder/logs/errorcountlog.txt", "r+", encoding="utf-8") as fout:
                count=int(fout.read())
                count = count+1
                fout.seek(0)
                if count>10:
                    fout.write(str(0))
                    self.SendEmail("Programmas darbībā konstatēts liels skaits kļūdu, vērts pārbaudīt logus!", 1)
                else:
                    fout.write(str(count))
                fout.truncate()
                
        


    ######################################## Crawler code #####################################################
    
    #sākuma punkts, norādītie urli tiks apmeklēti, katram izpildot 'parse' f-ju
    def start_requests(self):
        self.log("Script start", 1)
        urls = [
            'https://www.rdveikals.lv/search/lv/word/rx+5700/page/1/filters/437_0_0/',
            "https://www.rdveikals.lv/search/lv/word/rx+5600/page/1/",
            "https://www.rdveikals.lv/search/lv/word/rtx+3060/page/1/",
            "https://www.rdveikals.lv/search/lv/word/rx+6700/page/1/",
            'https://sb.searchnode.net/v1/query/docs?query_key=qJCQ7AEn9cNmcFozKKFfSJVXf90mtDD2&search_query=rx%205700&sort.0=-inStock&sort.1=-score&offset=0&limit=48&facets.0=attr_*',
            "https://sb.searchnode.net/v1/query/docs?query_key=qJCQ7AEn9cNmcFozKKFfSJVXf90mtDD2&search_query=rx%205600&sort.0=-inStock&sort.1=-score&offset=0&limit=48&facets.0=attr_*",
            "https://sb.searchnode.net/v1/query/docs?query_key=qJCQ7AEn9cNmcFozKKFfSJVXf90mtDD2&search_query=rtx%203060&sort.0=-inStock&sort.1=-score&offset=0&limit=48&facets.0=attr_*",
            "https://sb.searchnode.net/v1/query/docs?query_key=qJCQ7AEn9cNmcFozKKFfSJVXf90mtDD2&search_query=rx%206700&sort.0=-inStock&sort.1=-score&offset=0&limit=48&facets.0=attr_*",
            "https://www.dateks.lv/meklet?q=rx%205700",
            "https://www.dateks.lv/meklet?q=rx%205600",
            "https://www.dateks.lv/meklet?q=rtx%203060",
            "https://www.dateks.lv/meklet?q=rx%206700",
            "https://220.lv/lv/datortehnika/datoru-komponentes/videokartes-gpu",
            "https://oreol.eu/search/?search=5700%20xt&description=true",
            "https://oreol.eu/search/?search=rtx%203060&description=true",
            "https://oreol.eu/search/?search=rx%206700&description=true",
            "https://www.balticdata.lv/lv/datoru-komponentes/videokartes",
            "https://www.balticdata.lv/lv/datoru-komponentes/videokartes/2",
            "https://www.balticdata.lv/lv/datoru-komponentes/videokartes/3",
            "https://www.balticdata.lv/lv/datoru-komponentes/videokartes/4",
            "https://www.balticdata.lv/lv/datoru-komponentes/videokartes/5"
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
        elif "oreol" in str(response.url):
            self.processOreol(response)
        elif "balticdata" in str(response.url):
            self.processBalticdata(response)
        return
        
    
    def processRDVeikals(self, response):
        responseData=str(response.text)
        self.log("Processing RD Veikals")
        try:
            soup = BeautifulSoup(str(responseData), 'html.parser')
        except Exception as e:
            print("Error parsing the page")
            self.log(content="Error parsing the page: " + str(e), isError=1)

        try:
            results = soup.find('div', {"id": "main_container_wrapper"}).find('ul', 'product-list')
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
            self.log(content="Could not find the result 'ul': " + str(e), isError=1)

        resListElements = results.find_all('div', 'product__info')
        found=False
        msgText="Veikalā RD Electronics tika atrastas sekojošas preces:\n\n"

        for el in resListElements:
            try:
                prodInfo=str(el.find('div', 'product__info__part').find('h3', 'product__title').find('a').text).strip()
                link=str(el.find('div', 'product__info__part').find('h3', 'product__title').find('a')['href']).strip()
                link="https://www.rdveikals.lv/"+link
                price=str(el.find('p', 'price').text).strip()
                for prod in self.product:
                    #meklēšanas rezultāti satur vajadzīgo preci  - izvelkam saiti, cenu un sūtam epastu ar info:
                    if prod in prodInfo and "portatīvais" not in link.lower():
                        print("Found the product!")
                        found=True
                        msgText=msgText + prodInfo + "\nSaite: "+ link + "\nCena: " + price + "\n\n"
                        self.log("Found the product " + prodInfo + " for " + price + ". Available: " + link + ". Sending email..")
                   
                #print(prodInfo + ' ' + price + ' ' + link)

            except Exception as e:
                self.log(content="Failed to process a search result: " + str(e), isError=1)
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
            self.log(content="Failed to parse json: " + str(e), isError=1)
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
                price=r["priceDefault"]
                for prod in self.product:
                    #specifiska atlase, jo 1A pārdod cooling produktus konkrētajai videokartei, kas nav vajadzīgi
                    if prod in title and "water" not in title.lower() and "samos" not in title.lower() and r["inStock"] == True:
                        if int(price)>self.max_price:
                            self.log("Too expensive: " + prod + " for " + str(price))
                        else:
                            url=r["url"]
                            url="https://www.1a.lv"+url
                            print(title + " " + str(price) + " " + url)
                            self.log("Found the product " + title + " for " + str(price) + ". Available: " + url + ". Sending email..")
                            msgText=msgText + title + "\nSaite: "+ url + "\nCena: " + str(price) + "\n\n"   
                            found=True
                #print(title)

            except Exception as e:
                self.log(content="Failed to process a search result: " + str(e), isError=1)
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
            self.log(content="Error parsing the page: " + str(e), isError=1)

        try:
            results = soup.find('div', 'page')
            resListElements = results.find_all('div', 'prod')
        except Exception as e:
            print("Failed to parse the search results")
            self.log(content="Failed to parse the search results" + str(e), isError=1)

        
        found=False
        msgText="Veikalā Dateks tika atrastas sekojošas preces:\n\n"
        pattern = re.compile(r'\s+')

        for el in resListElements:
            try:
                prodInfo=str(el.find('div', 'name').text).strip()
                link=str(el.find('div', 'top').find('a')['href']).strip()
                price=re.sub(pattern, '',str(el.find('div', 'mid').find('div', 'price').text).strip()[:-5])
                for prod in self.product:
                    if prod in prodInfo and "water" not in prodInfo.lower() and "ryzen" not in prodInfo.lower() and "coolers" not in link.lower() and "personalie-datori" not in link.lower() and "portativie-datori" not in link.lower() and "datorkomplekti" not in link.lower():
                        if int(price)>self.max_price:
                            self.log("Too expensive: " + prodInfo + " for " + str(price))
                        else:
                            print("Found " + prod)
                            found=True
                            link="https://www.dateks.lv"+link
                            msgText=msgText + prodInfo + "\nSaite: "+ link + "\nCena: " + price + "\n\n"
                            self.log("Found the product " + prodInfo + " for " + price + ". Available: " + link + ". Sending email..")
                    
                #print(prodInfo)

            except Exception as e:
                self.log(content="Failed to process a search result: " + str(e), isError=1)
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
            self.log(content="Error parsing the page: " + str(e), isError=1)

        try:
            results = soup.find('div', {"id": "productListLoader"})
            resListElements = results.find_all('div', 'product-list-item')
        except Exception as e:
            print("Failed to parse the search results")
            self.log(content="Failed to parse the search results" + str(e), isError=1)

        
        found=False
        msgText="Veikalā 220.lv tika atrastas sekojošas preces:\n\n"

        for el in resListElements:
            try:
                el = el.find('p', 'product-name')
                if el == None:          #fix situācijai, kad 220 ieliek reklāmu starp rezultātiem
                    continue
                prodInfo=str(el.text).strip()
                available=el.find('span', 'label-soldout')
                for prod in self.product:
                    if prod in prodInfo and available == None:
                        print("Found " + prod)
                        found=True
                        link=str(el.find('p', 'product-name').find('a')['href']).strip()
                        price=str(el.find('div', 'product-price').find('span', 'price notranslate').text).strip()
                        msgText=msgText + prodInfo + "\nSaite: "+ link + "\nCena: " + price + "\n\n"
                        self.log("Found the product " + prodInfo + " for " + price + ". Available: " + link + ". Sending email..")
                    
                #print(prodInfo)

            except Exception as e:
                self.log(content="Failed to process a search result: " + str(e), isError=1)
                pass

        if found == False:
            self.log("Didn't find the product")
        else:
            self.SendEmail(msgText, 0)

    
    def processOreol(self, response):
        responseData=str(response.text)
        self.log("Processing oreol.eu")
        try:
            soup = BeautifulSoup(str(responseData), 'html.parser')
        except Exception as e:
            print("Error parsing the page")
            self.log(content="Error parsing the page: " + str(e), isError=1)

        try:
            resListElements = soup.find_all('div', 'product-layout')
            if resListElements == None or resListElements==[]:
                self.log('No search results')
                return
        except Exception as e:
            print("Failed to parse the search results")
            self.log(content="Failed to parse the search results" + str(e), isError=1)
        
        found=False
        msgText="Veikalā oreol.eu tika atrastas sekojošas preces:\n\n"

        for el in resListElements:
            try:
                prodInfo=str(el.find('div', 'caption').find('a').text).strip()
                price=int(str(el.find('div', 'caption').find('p', 'price').text).strip()[:-4].replace(" ", ""))
                for prod in self.product:
                    if prod in prodInfo and "microsd" not in prodInfo.lower():
                        if price > self.max_price:
                            self.log("Too expensive: " + prodInfo + " for " + str(price))
                        else:
                            print("Found " + prod)
                            found=True
                            link=str(el.find('div', 'caption').find('a')['href']).strip()
                            msgText=msgText + prodInfo + "\nSaite: "+ link + "\nCena: " + str(price) + "\n\n"
                            self.log("Found the product " + prodInfo + " for " + str(price) + ". Available: " + link + ". Sending email..")
                    
                #print(prodInfo + ' ' + str(price))

            except Exception as e:
                self.log(content="Failed to process a search result: " + str(e), isError=1)
                pass

        if found == False:
            self.log("Didn't find the product")
        else:
            self.SendEmail(msgText, 0)

    def processBalticdata(self, response):
        responseData=str(response.text)
        self.log("Processing balticdata")
        try:
            soup = BeautifulSoup(str(responseData), 'html.parser')
        except Exception as e:
            print("Error parsing the page")
            self.log(content="Error parsing the page: " + str(e), isError=1)

        try:
            resListElements = soup.find_all('div', 'EBI4ProductObjectPlate')
            if resListElements == None or resListElements==[]:
                self.log('No search results')
                return
        except Exception as e:
            print("Failed to parse the search results")
            self.log(content="Failed to parse the search results" + str(e),  isError=1)
        
        found=False
        msgText="Veikalā balticdata tika atrastas sekojošas preces:\n\n"

        for el in resListElements:
            try:
                prodInfo=str(el.find('div', 'EBI4ProductObjectPlateTitle').find('a').text).strip()
                price=int(str(el.find('div', 'EBI4ProductObjectPlatePrices').find('div', 'EBI4ProductObjectPlatePriceSale').text).strip()[:-5].replace(" ", ""))
                availability=str(el.find('div', 'EBI4ProductObjectButtonCompare').find('a').text).strip().lower()
                for prod in self.product:
                    if prod in prodInfo and availability != "prece nav noliktavā":
                        if price>self.max_price:
                            self.log("Too expensive: " + prodInfo + " for " + str(price))
                        else:
                            print("Found " + prod + ' ' +  str(price))
                            found=True
                            link=str(el.find('div', 'EBI4ProductObjectPlateTitle').find('a')['href']).strip()
                            link="https://www.balticdata.lv"+link
                            msgText=msgText + prodInfo + "\nSaite: "+ link + "\nCena: " + str(price) + "\n\n"
                            self.log("Found the product " + prodInfo + " for " + str(price) + ". Available: " + link + ". Sending email..")
                #print(prodInfo + ' ' + str(price))

            except Exception as e:
                self.log(content="Failed to process a search result: " + str(e), isError=1)
                pass

        if found == False:
            self.log("Didn't find the product")
        else:
            self.SendEmail(msgText, 0)
