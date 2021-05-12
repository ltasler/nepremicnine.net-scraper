#!/usr/bin/python

import sys
from lxml import html
from time import sleep
from datetime import datetime
import requests
import argparse
import json as jsonOld
import ujson as json
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Scraper:
    
    _appdata = {}
    _appdata_file = ''
    
    def __init__(self, appdata_file):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print("=============== Scraper started at " + timestamp + " ===============")
        print("Opening appdata file: " + appdata_file)
        with open(appdata_file, "r") as file:
            appdata = json.load(file)
        if not appdata:
            raise FileNotFoundError(f"Could not load {appdata_file}.")
        self._appdata = appdata
        self._appdata_file = appdata_file
        # print("appdata file open")
    
    def _check_for_removed(self):
        """
        Checks for removed urls.
        :return: return array of links to removed ones.
        """
        print("Checking for removed links...")
        visited = self._appdata["visited"]
        removed = []
        for i, v in enumerate(visited):
            url = v["link"]
            r = requests.get(url)
            if r.status_code == 404:
                # Does not exist anymore. Remove and append for report.
                removed.append(v)
                del self._appdata['visited'][i]
        print("Removed " + removed.__len__().__str__())
        return removed
    
    def _does_offer_exists(self, offer_id):
        """
        Checks if offer id exists in
        :return: True if found false otherwise
        """
        visited = self._appdata["visited"]
        for v in visited:
            if v["id"] == offer_id:
                return True
        return False
    
    @staticmethod
    def _get_page_number(url):
        tmp = re.search(r"/[0-9]/", url).group(0)
        return int(tmp[1:2])
    
    def _check_for_new(self, url):
        """
        Checks for new offers on url in appdata.
        :return:
        """
        new_offers = []
        page_number = self._get_page_number(url)
        while True:             # Fake do while
            # print("Checking page " + page_number.__str__() + " url: " + url)
            # print("Checking page " + page_number.__str__())
            page = requests.get(url)
            page_tree = html.fromstring(page.content)
            offers = page_tree.xpath('//div[@class="seznam"]/div[@itemprop="itemListElement"]')
            
            if len(offers) == 0:
                # Koncni pogoj za while loop. Nimamo vec ponudb
                break
            
            for offer in offers:
                offer_id = offer.xpath('attribute::id')[0]
                if self._does_offer_exists(offer_id):
                    # Ponuba obstaja, preskoci
                    continue
                
                title = offer.xpath("div/h2/a/span/text()")[0]
                link = f'{self._appdata["baseUrl"]}{offer.xpath("div/h2/a/attribute::href")[0]}'
                offer_type = offer.xpath('div/div/span/span[@class="tipi"]/text()')[0]
                desc = offer.xpath('div/div/div[@class="kratek_container"]/div/text()')[0]
                size = offer.xpath('div/div/div[@class="main-data"]/span[@class="velikost"]/text()')[0]
                price = offer.xpath('div/div/div[@class="main-data"]/span[@class="cena"]/text()')[0]
                agency = offer.xpath('div/div/div[@class="main-data"]/span[@class="agencija"]/text()')[0]
                
                # Imamo vse podatke pa jih se vpisimo
                o = {
                    "id": offer_id,
                    "title": title,
                    "link": link,
                    "type": offer_type,
                    "desc": desc,
                    "size": size,
                    "price": price,
                    "agency": agency,
                }
                new_offers.append(o)
                self._appdata["visited"].append(o)
            # End of for
            
            # na koncu se "gremo na naslednjo stran"
            page_number = page_number + 1
            url = re.sub(r"/([0-9]|[1-9][0-9]|[1-9][0-9][0-9])/", f"/{page_number}/", url)

            
            # Spimo 2 sekundi, da slucaaaaaaaaaaaajno ne bomo dos-al
            sleep(2)
            
        # End of while
        return new_offers
    # End of _check_for_new
    
    @staticmethod
    def _get_item_text_message(n):
        # Presledek po linku poskrbi, da mail klient pomotoma ne vkljuci zacetek opisa v URL
        message_text = f'{n["title"]}\n{n["link"]} \n{n["desc"]}\nTip: {n["type"]}\n'
        message_text += f'Velikost:{n["size"]}\nCena: {n["price"]}\nAgencija: {n["agency"]}\n\n'
        return message_text
    
    def send_mail(self, new, removed):
        if len(new) == 0 and len(removed) == 0:
            # Ce ni nic novega ne posiljaj..
            return False
        print("Sending mail...")
        smtp = self._appdata["smtp"]
        port = smtp["port"]
        user = smtp["user"]
        password = smtp["password"]
        smtp_server = smtp["server"]
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Spremembe na nepremicnine.net"
        message["From"] = user
        message["To"] = ', '.join(self._appdata["mailRecipients"])
        
        message_text = "Pozdravljen/a,\n\nPrinasam novice iz nepremicnine.net.\n\n\n"
        if len(new) > 0:
            message_text += "Novi oglasi na nepremicnine.net:\n\n"
            for n in new:
                message_text += self._get_item_text_message(n)
            message_text += "-------------------------------------------------------------------------\n\n"
        if len(removed) > 0:
            message_text += "Odstranjeni oglasi na nepremicnine.net\n\n"
            for r in removed:
                message_text += self._get_item_text_message(r)
            message_text += "-------------------------------------------------------------------------\n\n"
        
        message_text += "Lep Pozdrav,\nMr. robotek."
        
        part1 = MIMEText(message_text, "plain")
        # TODO: Do the html MIME
        message.attach(part1)
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(user, password)
            server.sendmail(user, self._appdata["mailRecipients"], message.as_string())
        return True
    
    def run(self, nomail):
        removed = self._check_for_removed()
        new = []
        for url in self._appdata["urls"]:
            print("Checking URL: " + url)
            found = self._check_for_new(url)
            print("New found: " + found.__len__().__str__())
            new.extend(found)

        print("New combined: " + new.__len__().__str__())

        success = True
        if not nomail:
            # poslji mail
            success = self.send_mail(new, removed)
        
        # Prejsni funkciji niso cisti, spreminjajo appdata, ki ga bomo sedaj zapisali nazaj za prihodnja izvajanja
        if success:
            print("Writing appdata file")
            # Spreminjaj samo ce je bilo uspesno posiljanje
            with open(self._appdata_file, 'w') as f:
                json.dump(self._appdata, f, indent=2)

    def purge(self):

        self._appdata["visited"].clear()

        with open(self._appdata_file, 'w') as f:
            json.dump(self._appdata, f, indent=2)

        print("Visited list purged")

        
        
APPDATA_FILE = "appdata.json"


def main(argv):
    # Construct the argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument('--purge', action='store_true', help="Purges the visited database in the appdata.json")
    ap.add_argument('--nomail', action='store_true', help="Doesn't send the email, just saves the visited to appdata.json")
    args = ap.parse_args(argv)

    scraper = Scraper(APPDATA_FILE)
    if args.purge:
        scraper.purge()
    else:
        scraper.run(args.nomail)
    

if __name__ == '__main__':
    sys.path.extend(['.', '..'])
    main(sys.argv[1:])
