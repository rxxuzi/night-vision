import hashlib
from bs4 import BeautifulSoup
import os


def extract_links(html_content: str) -> list:
    soup = BeautifulSoup(html_content, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    return links


class Shallot:
    def __init__(self, s_id: int, url: str, headers: dict, html_content: str, sl_hash: str):
        self.id = s_id
        self.hash = sl_hash
        self.url = url
        self.headers = headers
        self.links = extract_links(html_content)
        self.html_content = html_content

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'hash': self.hash,
            'url': self.url,
            'headers': self.headers,
            'links': self.links,
            'html_content': self.html_content
        }

    def save(self):
        filename = f"{self.id}.html".replace(" ", "_")
        abs_path = os.path.abspath(filename)
        with open(abs_path, 'w', encoding='utf-8') as file:
            file.write(self.html_content)
        print(f"Saved {self.url} as {abs_path}")

    def __str__(self):
        return f"Shallot(ID:{self.id},URL:{self.url},HASH:{self.hash})"
