import requests
import threading
import queue
import os
from tqdm import tqdm

class ProxyScanner:
    def __init__(self, proxy_type, proxy_file, working_file):
        self.proxy_type = proxy_type
        self.proxy_file = proxy_file
        self.working_file = working_file
        self.proxies = self.load_proxies()
        self.num_scanned = 0
        self.num_working = 0
        self.lock = threading.Lock()

    def load_proxies(self):
        with open(self.proxy_file, "r") as f:
            proxies = f.read().splitlines()
        return proxies

    def save_working_proxy(self, proxy):
        with self.lock:
            with open(self.working_file, "a") as f:
                f.write(proxy + "\n")
            print("\033[92m[+] {} - {}\033[0m".format(self.proxy_type.upper(), proxy))

    def save_bad_proxy(self, proxy):
        print("\033[91m[-] {} - {}\033[0m".format(self.proxy_type.upper(), proxy))

    def check_proxy(self, proxy):
        try:
            requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=10)
            self.save_working_proxy(proxy)
            self.num_working += 1
        except:
            self.save_bad_proxy(proxy)
        finally:
            self.num_scanned += 1

    def scan_proxies(self):
        q = queue.Queue()
        for proxy in self.proxies:
            q.put(proxy)

        threads = []
        num_threads = min(800, len(self.proxies))

        for i in range(num_threads):
            t = threading.Thread(target=self.worker, args=(q,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def worker(self, q):
        while True:
            try:
                proxy = q.get(block=False)
            except queue.Empty:
                break
            self.check_proxy(proxy)

if __name__ == "__main__":
    proxy_types = ["http", "https", "socks4", "socks5"]
    working_files = {}

    # Set the default directory to C:\User\%USERNAME%\Documents\Proxies\
    dir_path = os.path.join(os.path.expanduser("~"), "Documents", "Proxies")

    # Iterate over each proxy type and file and start scanning
    for proxy_type in proxy_types:
        proxy_file = os.path.join(dir_path, "{}.txt".format(proxy_type))
        if os.path.exists(proxy_file):
            working_file = os.path.join(dir_path, "{}_working.txt".format(proxy_type))
            scanner = ProxyScanner(proxy_type, proxy_file, working_file)
            scanner.scan_proxies()
            working_files[proxy_type] = scanner.num_working

    # Print results
    print("\nProxy Scan Results:")
    for proxy_type, num_working in working_files.items():
        proxy_file = os.path.join(dir_path, "{}.txt".format(proxy_type))
        with open(proxy_file, "r") as f:
            num_total = len(f.read().splitlines())
        print("{} Proxies: {}/{}".format(proxy_type.capitalize(), num_working, num_total))
