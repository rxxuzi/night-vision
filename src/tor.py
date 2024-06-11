import time
import requests
import subprocess
from subprocess import Popen


class Tor:
    en_time = 0.0
    st_time = 0.0  # 開始時間 (マイクロ秒)

    def __init__(self, port: int = 9050, bin_path: str = "tor.exe"):
        self.process = None
        self.port = port
        self.path = bin_path

    def start(self) -> None:
        # Tor をバックグラウンドで起動
        self.process = Popen(self.path, stdout=subprocess.PIPE)
        Tor.st_time = time.time()
        print("Tor Start")

    def setup_proxy(self) -> requests.Session():
        session = requests.session()
        try:
            session.proxies = {
                'http': 'socks5h://localhost:' + str(self.port),
                'https': 'socks5h://localhost:' + str(self.port)
            }
        except Exception as e:
            print(f"Error setting up proxy: {e}")
        return session

    def kill(self):
        # 　プロセスの終了
        if self.process:
            self.process.terminate()
            self.process.wait()
        else:
            print("Tor process is not running.")

    def stat(self) -> str:
        if self.process and self.process.poll() is None:
            return "Tor process is running."
        else:
            return "Tor process is not running."

    def restart(self):
        self.kill()
        self.start()

    @staticmethod
    def uptime() -> float:
        if Tor.st_time == 0:
            return 0.0
        if Tor.en_time == 0:
            return time.time() - Tor.st_time
        return Tor.en_time - Tor.st_time

    def __str__(self) -> str:
        status = self.stat()
        uptime = Tor.uptime()
        return f"Tor({self.port}, {self.path}): {status}, Uptime: {uptime:.2f} seconds."
