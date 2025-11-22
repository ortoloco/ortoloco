import requests

from ortoloco import settings


def get_news_posts(wpcategory = 10):
    base = "https://news.ortoloco.ch/wp-json/wp/v2/"
    method = base + "posts?_fields=content.rendered,title&categories=" + str(wpcategory)
    response = None
    try:
        print(settings.WP_PASSWORD)
        response = requests.get(method, auth=(settings.WP_USER, settings.WP_PASSWORD), timeout=3)
    except Exception:
        pass
    if response:
        html = ''
        for post in response.json():
            html += '<h1 class="wp-title">' + post['title']['rendered'] + "</h1>"
            html += post['content']['rendered']
        return html
    return '<i>Fehler: Die Inhalte von news.ortoloco.ch konnten nicht geladen werden.</i>'
