import scrapy

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    
    # The first URLs to crawl
    start_urls = [
        'http://quotes.toscrape.com/page/1/',
        'http://quotes.toscrape.com/page/2/',
    ]

    # The method called to handle the response for each URL
    def parse(self, response):
        # response.css() uses CSS selectors to find elements
        for quote in response.css('div.quote'):
            # yield returns a dictionary representing the scraped item
            yield {
                'text': quote.css('span.text::text').get(), # ::text extracts only the text
                'author': quote.css('small.author::text').get(),
                'tags': quote.css('div.tags a.tag::text').getall(), # getall() for a list of all matching texts
            }

        # Handle pagination: Find the link to the next page and follow it
        next_page = response.css('li.next a::attr(href)').get()
        if next_page is not None:
            # response.follow automatically builds an absolute URL and schedules a new request
            yield response.follow(next_page, callback=self.parse)
            
# To run this from the project's root directory:
# scrapy crawl quotes -o quotes.json