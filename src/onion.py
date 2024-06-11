import hashlib
from queue import Queue
from threading import Thread, Lock
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from requests.sessions import Session
from requests.structures import CaseInsensitiveDict

from shallot import Shallot
from tor import Tor


def extract_redirect_url(full_url):
    # URLのクエリパラメータを解析
    parsed_url = urlparse(full_url)
    query_params = parse_qs(parsed_url.query)

    if 'redirect_url' in query_params:
        return query_params['redirect_url'][0]
    else:
        # 'redirect_url'キーがない場合は元のURLを返す
        return full_url


class Onion:
    def __init__(self, tor_instance: Tor, max_pages: int = 10, max_threads: int = 10, max_depth: int = 2):
        self.max_pages: int = max_pages  # 最大クローリングページ数
        self.max_threads: int = max_threads  # 最大スレッド数
        self.max_depth: int = max_depth  # 深さ
        self.tor: Tor = tor_instance  # Torクラスのインスタンス
        self.start_site = None  # 検索時にスタートするURL
        self.search_engine = None  # 検索エンジンのURL
        self.pages_crawled = 0  # クローリングしたページのカウント
        self.lock = Lock()
        self.queue = Queue()
        self.shallots: list[Shallot] = []  # Shallotインスタンスのリスト
        self.next_id = 0  # ShallotのためのユニークID
        self.hashes: dict[str, Shallot] = {}  # HTMLのハッシュ値を保存する辞書

    def set_searchengine(self, url: str) -> None:
        self.search_engine = url

    def crawl(self, onion_url: str) -> tuple[str, CaseInsensitiveDict[str]] | tuple[str, None]:
        session: Session = self.tor.setup_proxy()
        try:
            response = session.get(onion_url)
            response.raise_for_status()  # ステータスチェック
            return response.text, response.headers  # HTMLコンテンツとヘッダーを返す
        except requests.RequestException as e:
            return f"Request Error: {str(e)}", None
        except Exception as e:
            return f"Unexpected error: {str(e)}", None

    def dig(self, start_url: str, keyword: str):
        # クローリングの開始
        self.start_site = start_url
        self.queue.put(start_url)

        threads = []
        for _ in range(self.max_threads):
            thread = Thread(target=self.worker, args=(keyword,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def worker(self, keyword: str):
        # キーワードに基づくクローリングのワーカー

        # キューが空ではなく、クロールしたページ数が最大ページ数未満の間ループ
        while not self.queue.empty() and self.pages_crawled < self.max_pages:
            # キューからURLを取得
            url = self.queue.get()
            url = extract_redirect_url(url)

            # 指定されたURLをクロール
            result = self.crawl(url)
            html_content, headers = result
            # ハッシュ計算
            html_hash: str = hashlib.sha256(html_content.encode('utf-8')).hexdigest()

            if headers is not None and html_hash not in self.hashes:
                with self.lock:
                    # ページ数をカウントアップ
                    self.pages_crawled += 1
                    # ユニークなIDを取得し、次のIDに更新
                    current_id = self.next_id

                # 新しいShallotインスタンスを作成し、ハッシュ値を辞書に追加
                shallot = Shallot(current_id, url, headers, html_content, html_hash)
                self.shallots.append(shallot)
                self.hashes[html_hash] = shallot  # ハッシュ値とインスタンスを保存

                # HTMLコンテンツからリンクを抽出
                links = self.extract_links(html_content)
                # キーワードに基づいてリンクをフィルタリング
                filtered_links = self.filter_links(links, keyword)
                # フィルタリングされたリンクをキューに追加
                for link in filtered_links:
                    self.queue.put(link)
            else:
                # エラーが発生した場合、エラーメッセージを出力
                print(f"Error ID {current_id} : URL : {url}")

            self.next_id += 1  # インクリメント

    def search(self, keyword: str):
        # 指定されたキーワードで検索を実行し、クローリングを開始

        if not self.search_engine:
            print("Search engine URL is not set.")
            return

        search_url = f"{self.search_engine}{keyword}"
        print(f"Searching for [{keyword}] using {search_url}")

        self.dig(search_url, keyword)

    @staticmethod
    def extract_links(html_content: str) -> list:
        soup = BeautifulSoup(html_content, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        return links

    @staticmethod
    def filter_links(links, keyword):
        filtered_links = [link for link in links if keyword in link]
        return filtered_links

    def __str__(self) -> str:
        return f"Onion(max_pages={self.max_pages}, max_threads={self.max_threads}, start_site={self.start_site}, " \
               f"pages_crawled={self.pages_crawled})"
