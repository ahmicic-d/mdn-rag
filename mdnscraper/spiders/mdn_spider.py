import scrapy
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from mdnscraper.items import MdnPageItem

class MdnSpider(scrapy.Spider):
    
    name = "mdn_html"
    
    start_urls = [
        "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements",
        "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes",
        "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes",
        "https://developer.mozilla.org/en-US/docs/Web/HTML",
        "https://developer.mozilla.org/en-US/docs/Web/CSS",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "https://developer.mozilla.org/en-US/docs/Web/Accessibility",
        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers",
    ]
    
    allowed_domains = ["developer.mozilla.org"]
    
    custom_settings = {
        "CLOSESPIDER_PAGECOUNT": 600,
        "DEPTH_LIMIT": 5,             
        "DEPTH_PRIORITY": 1,         
        "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
        "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
    }

    SKIP_URL_PATTERNS = [
        "/en-US/docs/MDN/",
        "/en-US/docs/Glossary/",
        "/en-US/blog/",
        "/en-US/curriculum/",
        "/en-US/observatory/",
        "/en-US/plus/",
        "/en-US/docs/Web/API",
        "/de/docs/", "/es/docs/", "/fr/docs/",
        "/ja/docs/", "/ko/docs/", "/pt-BR/docs/",
        "/ru/docs/", "/zh-CN/docs/", "/zh-TW/docs/",
        "?q=",
        "#",
        "contributors.txt",
        ".txt",
    ]

    ALLOWED_URL_PATTERNS = [
        "/en-US/docs/Web/HTML",
        "/en-US/docs/Web/CSS",
        "/en-US/docs/Web/JavaScript",
        "/en-US/docs/Web/Accessibility",
        "/en-US/docs/Web/HTTP",
    ]

    def parse(self, response):
        url = response.url

        #Pregledavamo da li moramo preskočiti ovu stranincu
        if self._should_skip(url):
            self.logger.debug(f"Skipping: {url}")
            return
        
        #Ekstrakcija stranice, ako vrati None stranica je prazna, yield item šalje dalje za daljnju obradu
        item = self._extract_content(response)
        if item:
            yield item

        #Dohvaćamo sve href atribute kao listu stringova, pretvaramo sve u apsolutne URL-ove (urljoin())
        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            #Ako je link valjan, follow kreira novi zahtjev - automatski se vodi evidencija već posjećenih linkova 
            if self._is_valid_link(full_url):
                yield response.follow(full_url, callback = self.parse)
        
    
    #Provjera da li je url neki od prethodno definiranih patterna koje treba preskočiti
    def _should_skip(self, url:str) -> bool:
        return any(pattern in url for pattern in self.SKIP_URL_PATTERNS)
    
    def _is_valid_link(self, url:str) -> bool:
        if "developer.mozilla.org" not in url:
            return False
        return any(pattern in url for pattern in self.ALLOWED_URL_PATTERNS)
    

    def _extract_content(self, response) -> MdnPageItem | None:
        
        soup = BeautifulSoup(response.text, "lxml")

        #Dijelove koje izbacujem, radi zbunjivanja RAG-a
        NOISE_SELECTORS = [
            "nav",
            "footer",
            "header",
            ".sidebar",
            ".sidebar-inner",
            ".top-navigation",
            ".breadcrumbs",
            "aside",
            ".prev-text",
            ".contributors",
            "[aria-label = 'Breadcrumb']",
            ".document-toc-container",
            "script",
            "style",
        ]

        #Izbacijvanje elemenata koji se nalaze u NOISE_SELECTORS
        for selector in NOISE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()
        
        #Vraća prvi HTML element koji sadrži h1 tag, sprema ga u title_element -> uzimamo samo tekst i brišemo praznine (strip = True) te spremamo unutar title
        #Ako nema teksta, vraća prazni string
        title_element = soup.select_one("h1")
        title = title_element.get_text(strip = True) if title_element else ""

        #Ako stranica nema h1 preskačemo je
        if not title:
            self.logger.warning(f"No title for: {response.url}")
            return None
        
        #Spremanje breadcrumb-a u posebnu varijablu
        breadcrumb = self._extract_breadcrumb(response)
        #Spremanje sekcija stranice (HTML, CSS, JS)
        section = self._detect_section(response.url)

        #List comprehension prolazi kroz sve h2 i h3, rezultat je lista rječnika [{"level": "h2", "text": "..."}, {"level": "h3", "text": "...."}]
        headings = [
            {"level": h.name, "text": h.get_text(strip = True)}
            for h in soup.select("h2, h3")
        ]

        #Obuhvati content koji spada pod barem jednim od ovih selektora
        main_content = soup.select_one("article, main, .main-page-content, #content, .content-container")

        #Fallback ako ne nadjemo ništa, uzimamo cijeli body (nisam siguran koliko je ovo dobra praksa)
        if not main_content:
            main_content = soup.select_one("body")

        #"Čistimo tekst" -> mičemo Whitespace, prazne linije - Ako content ima manje od 100 charactera ignoriramo ju zbog irelevancije
        clean_text = self._to_clean_text(main_content)
        if len(clean_text) < 100:
            self.logger.info(f"Too little content for: {response.url}")
            return None

        #Kreiramo jedan zapis od scrape-anoj stranici u kojem imamo URL, naslov, sekciju, breadcrumb, glavni sadržaj, listu podnaslova i vrijeme scrape-anja
        item = MdnPageItem()
        item["url"] = response.url
        item["title"] = title
        item["section"] = section
        item["breadcrumb"] = breadcrumb
        item["content"] = clean_text
        item["headings"] = headings
        item["scraped_at"] = datetime.now(timezone.utc).isoformat()

        return item
    

    #Funkcija pretvara HTML u tekst za RAG
    def _to_clean_text(self, element) -> str:
        
        #get_text() ignorira br, zato ga mijenjamo sa \n
        for br in element.find_all("br"):
            br.replace_with("\n")

        
        #Prije svakog block elementa, nadodajem \n - get_text() samo skuplja tekst, ne odvaja blokove (moguće spajanje dva odlomka u jedan)
        BLOCK_ELEMENTS = [
            "p",
            "div",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "blockquote",
            "pre",
            "section",
            "article",
            "dt",
            "dd"
        ]
        for tag in element.find_all(BLOCK_ELEMENTS):
            tag.insert_before("\n")

        
        for code_block in element.find_all(["pre", "code"]):
            code_block.decompose()

        #Dohvaćanje teksta
        text = element.get_text(separator = " ")

        #Čistimo whitespace, splitlines() odvaja linije (npr jedna ispod druge), strip() miče razmak, tab, newline
        #sprema se u polje lines sa jednom linijom razmaka
        lines =  []
        for line in text.splitlines():
            line = line.strip()
            if line:
                lines.append(line)
        
        clean = "\n\n".join(lines)

        return clean
    

    #Metoda koja ekstrahira breadcrumb elemente i vraća listu stringova npr. ["WEB", "HTML", "CSS"]
    def _extract_breadcrumb(self, response) -> list[str]:
        breadcrumb = response.css(
            "[aria-label = 'Breadcrumb'] a::text, "
            ".breadcrumbs a::text, "
            "nav[aria-label = 'breadcrumb'] a::text"
        ).getall()
        return [b.strip() for b in breadcrumb if b.strip()]
    

    #Metoda koja vraća kategoriju u koju neki sadržaj može spadati
    def _detect_section(self, url: str) -> str:
        if "/Web/HTML" in url:
            return "HTML"
        elif "/Web/CSS" in url:
            return "CSS"
        elif "/Web/JavaScript" in url:
            return "JavaScript"
        elif "/Web/API" in url:
            return "Web API"
        elif "/Web/Accessibility" in url:
            return "Accessibility"
        elif "/Web/HTTP" in url:
            return "HTTP"
        return "Other"