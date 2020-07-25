# Nepremicnine.net scraper

## Motivacija
Program je nastal, ker stanovanja izginejo iz neremičnine.net hitreje kot bi rekel keks. Enostavna rešitev, 
da ni potrebno gledati neprestano, če je kak nov oglas - s pomočjo tega programa si lahko redno obveščen o 
novih pondubah, kot tudi o vseh odstranjenih. Najbolje deluje, če program zaganja kakšen cron (unix) ali scheduled 
task (windows) na 
napravi, ki je neprestano prižgana. Ker program pošilja nove podatke samo v primeru, če pride do kakšne
spremebe, se lahko varno nastavi na interval recimo 5 minut brez da bi pospamal mailbox.

## Namestitev in uporaba
1. Inštalirati python. Testirano na verziji 3.7.2.
2. (opcijsko) Priporočljivo je narediti virtualni enviroment. Več o tem na https://docs.python-guide.org/dev/virtualenvs/, oz za MacOs: https://opensource.com/article/19/5/python-3-default-mac
3. Inštalirati requirements. To lahko storite z naslednjim ukazom: `pip install -r requirements.txt`
4. Kreirati file `appdata.json`. Ta file mora izgledati tako, kot je priložen primer `appdata_example.json`.
Vsa podana polja so obvezna:
    1. `baseUrl` - Osnovni url. To lahko pustite kar `https://www.nepremicnine.net`
    2. `urls` - Seznam urljev do prve strani vašega query-ja, ki vas zanima. Do tega url-ja pridete tako, da greste na spletno 
    stran in vnesete v iskalnik vse kriterije, ki vas zanimajo. Pomembno je, da url, ki ga kopirate je url od prve 
    strani, sicer bo program prejšnje strani spregledal. Primer je:
    `https://www.nepremicnine.net/oglasi-oddaja/ljubljana-mesto/stanovanje/1.5-sobno,2-sobno,2.5-sobno,3-sobno,3.5-sobno/cena-do-600-eur-na-mesec/1/?s=3`,
    pri cemer je pomembno da url vkljucuje tudi `/1/`. `?s=3` Oznacuje sortiranje, ni pa nujno za iskalnik. 
    3. `smtp` - podatki o vašem smtp strežniku. Za najlažjo uporabo priporočam, da kar uporabite googlov smtp 
    strežnik. Za prijavo se lahko kreira dodaten račun ali pa uporabi obstoječega.
        1. `port` - port od smtp strežnika.
        2. `server` - hostname smtp strežnika.
        3. `user` - račun, ki je uporabljen za prijavo na strežnik. Iz tega naslova se bodo tudi pošiljali maili.
        4. `password` - geslo računa uporabljeno za prijavo na stmp strežnik.
    4. `mailRecipients` - Seznam vseh ljudi, ki želite, da prejmejo te maile z novimi ponudbami.
    5. `visited` - To naj bo kar prazen seznam. Tu se bodo shranili podatki o vseh obiskanih oglasih. V bistvu je 
    polje uporabljeno kot neke vrste nosql baza.
5. Zaženi program s ukazom `python scraper.py`.
6. Za bolj avtomatizirano uporabo, se lahko uporabi task scheduler na windowsih oz. crontab na unix sistemih. 
Interval zagona se lahko nastavi po želji.

