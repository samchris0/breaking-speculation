from google_news_feed import GoogleNewsFeed

def get_top_headlines():
    gnf = GoogleNewsFeed(language='en',country='US')
    headlines = gnf.top_headlines()
    
    return headlines