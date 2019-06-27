#!/usr/bin/python

from lxml import html
from time import sleep
import requests
import json
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Scraper:
    
    _appdata = {}
    _appdata_file = ''
    
    def __init__(self, appdata_file):
        with open(appdata_file, "r") as file:
            appdata = json.load(file)
        if not appdata:
            raise FileNotFoundError(f"Could not load {appdata_file}.")
        self._appdata = appdata
        self._appdata_file = appdata_file
    
    def _check_for_removed(self):
        """
        Checks for removed urls.
        :return: return array of links to removed ones.
        """
        visited = self._appdata["visited"]
        removed = []
        for i, v in enumerate(visited):
            url = v["link"]
            r = requests.get(url)
            if r.status_code == 404:
                # Does not exist anymore. Remove and append for report.
                removed.append(v)
                del self._appdata['visited'][i]
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
    
    def _check_for_new(self):
        """
        Checks for new offers on url in appdata.
        :return:
        """
        new_offers = []
        url = self._appdata["url"]
        page_number = self._get_page_number(url)
        while True:             # Fake do while
            page = requests.get(url)
            page_tree = html.fromstring(page.content)
            offers = page_tree.xpath('//div[@class="seznam"]/div[@itemprop="itemListElement"]')
            
            if len(offers) == 0:
                # Koncni pogoj ya while loop. nimamo vec ponudb
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
            url = re.sub(r"/[0-9]/", f"/{page_number}/", url)
            
            # Spimo 2 sekundi, da slucaaaaaaaaaaaajno ne bomo dos-al
            sleep(2)
            
        # End of while
        return new_offers
    # End of _check_for_new
    
    @staticmethod
    def _get_item_text_message(n):
        message_text = f'{n["title"]}\n{n["link"]}\n{n["desc"]}\nTip: {n["type"]}\n'
        message_text += f'Velikost:{n["size"]}\nCena: {n["price"]}\nAgencija: {n["agency"]}\n\n'
        return message_text
    
    def send_mail(self, new, removed):
        if len(new) == 0 and len(removed == 0):
            # Ce ni nic novega ne posiljaj..
            return False
        
        smtp = self._appdata["smtp"]
        port = smtp["port"]
        user = smtp["user"]
        password = smtp["password"]
        smtp_server = smtp["server"]
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Spremembe na nepremicnine.net"
        message["From"] = user
        message["To"] = ','.join(self._appdata["mailRecipients"])
        
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
            server.sendmail(user, message["To"], message.as_string())
        return True
    
    def run(self):
        removed = self._check_for_removed()
        new = self._check_for_new()

        # poslji mail
        success = self.send_mail(new, removed)
        
        # Prejsni funkciji niso cisti, spreminjajo appdata, ki ga bomo sedaj zapisali nazaj za prihodnja izvajanja
        if success:
            # Spreminjaj samo ce je bilo uspesno posiljanje
            with open(self._appdata_file, 'w') as f:
                json.dump(self._appdata, f, indent=2)
        
        
APPDATA_FILE = "appdata.json"


def main():
    scraper = Scraper(APPDATA_FILE)
    scraper.run()
    

if __name__ == '__main__':
    main()
