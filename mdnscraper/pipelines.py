# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
import os
from datetime import datetime


class TextCleaningPipeline:

    LEGAL_PHRASES = [
        "Your Blueprint for a Better Internet",
        "MDN web Docs",
        "Mozilla Corporation",
        "Mozilla Foundation",
        "© 2005-",
        "Terms and Conditions",
        "Privacy Policy"
        "Cookie Policy"
    ]

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        content = adapter.get("content", "")
        lines = content.split("\n")

        #Dekomponiranje teksta na linije, filtriranje linija koje sadrže LEGAL_PHRASE, vraćamo očišćeni tekst
        clean_lines = [
            line for line in lines
            if not any(phrase in line for phrase in self.LEGAL_PHRASES)           
        ]
        adapter["content"] = "\n".join(clean_lines).strip()
        return item

class JsonlOutputPipeline:
    def open_spider(self, spider):

        os.makedirs("output", exist_ok=True)    #Direktorij unutar kojeg će se spremati scrape-ani podaci
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S") #Timestamp scrape-anja pojedinog dokumenta
        filepath = f"output/mdn_dataset_{timestamp}.json1"  #Izrada dokumenta pomoću timestampa (izbjegavanje overwrite-a)
        self.file = open(filepath, "w", encoding="utf-8")   #Otvaranje dokumenta za upisivanje scrape-anih podataka, self.file ostaje dostupan drugim metodama

    def close_spider(self, spider):
        self.file.close()


    #Metoda prima jedan item (npr. url, title, section, content sa pripadnim tekstovima), adapter "wrappa" item - omogućava rad nad itemom bez obzira na strukturu
    #dict(spider) pretvara adapter u rječnik (key-value par), json.dumps() pretvara taj rječnik u json string
    #Zapisujemo taj json string u datoteku
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        line = json.dumps(dict(adapter), ensure_ascii=False)
        self.file.write(line + "\n")
        return item

