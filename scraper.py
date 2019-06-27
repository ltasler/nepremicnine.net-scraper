from lxml import html
import requests
import json
import re


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
        for v, i in enumerate(visited):
            url = v["url"]
            r = requests.get(url)
            if r.status_code == 404:
                # Does not exist anymore. Remove and append for report.
                removed.append(v)
                del visited[i]  # TODO: Test that shit
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
    
    def _get_page_number(self, url):
        tmp = re.search(r"\/[0-9]\/", url).group(0)
        return int(tmp[1:2])

    
    def _check_for_new(self):
        """
        Checks for new offers on url in appdata.
        :param appdata:
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
            url = re.sub(r"\/[0-9]\/", f"/{page_number}/", url)
        #End of while
        return new_offers
    # End of _check_for_new
    
    def send_mail(self):
        return True
    
    def run(self):
        removed = self._check_for_removed()
        new = self._check_for_new()

        # poslji mail
        success = self.send_mail()
        
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
