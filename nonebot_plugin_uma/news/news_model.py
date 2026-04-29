class NewsItem:
    def __init__(self, server: str, news_id, news_time: str, news_url: str, news_title: str):
        self.server = server
        self.news_id = news_id
        self.news_time = news_time
        self.news_url = news_url
        self.news_title = news_title
        self.show_url = "▲" + self.news_url
