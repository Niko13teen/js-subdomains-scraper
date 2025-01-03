import os
import requests
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse, urljoin
import re
import argparse
from tqdm import tqdm
from colorama import Fore

domain_regex = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
banner = r"""
     ██╗███████╗███████╗██╗   ██╗██████╗ ██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗
     ██║██╔════╝██╔════╝██║   ██║██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║
     ██║███████╗███████╗██║   ██║██████╔╝██║  ██║██║   ██║██╔████╔██║███████║██║
██   ██║╚════██║╚════██║██║   ██║██╔══██╗██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║
╚█████╔╝███████║███████║╚██████╔╝██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║
 ╚════╝ ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝
                                                                                
███╗   ██╗███████╗███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗       
████╗  ██║██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗      
██╔██╗ ██║███████╗███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝      
██║╚██╗██║╚════██║╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗      
██║ ╚████║███████║███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║      
╚═╝  ╚═══╝╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝                                                                    
"""

def get_links_from_page(url, domain):
    links = set()
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(url, a_tag['href'])
            if urlparse(link).netloc == domain:
                links.add(link)
    except requests.RequestException as e:
        print(f"Ошибка при запросе к {url}: {e}")
    return links

def find_subdomains_in_js_and_save(url):
    subdomains = set()
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        for script in soup.find_all('script', src=True):
            js_url = urljoin(url, script['src'])
            try:
                js_response = requests.get(js_url)
                matches = domain_regex.findall(js_response.text)
                for match in matches:
                    subdomains.add((match, js_url))
                
                os.makedirs("scripts", exist_ok=True)
                filename = os.path.join("scripts", os.path.basename(js_url))
                with open(filename, 'wb') as f:
                    f.write(js_response.content)
            except requests.RequestException as e:
                print(f"Ошибка при запросе к {js_url}: {e}")
    except requests.RequestException as e:
        print(f"Ошибка при запросе к {url}: {e}")
    return subdomains

def crawl_website(start_url):
    domain = urlparse(start_url).netloc
    visited = set()
    queue = deque([start_url])
    sitemap = set()

    while queue:
        current_url = queue.popleft()
        if current_url not in visited:
            visited.add(current_url)
            sitemap.add(current_url)

            links = get_links_from_page(current_url, domain)
            for link in links:
                if link not in visited:
                    queue.append(link)

    return sitemap

def save_results_to_file(subdomains_in_js, sitemap, filename='results.txt'):
    with open(filename, 'w') as f:
        f.write("Список посещенных страниц:\n")
        for url in sitemap:
            f.write(url + '\n')
        
        f.write("\nНайдено в js файлах:\n")
        for subdomain, js_url in subdomains_in_js:
            f.write(f"{subdomain}, найдено в {js_url}\n")

def main():
    print(banner)
    print(f"{Fore.BLUE}Инструмент: {Fore.YELLOW}js-subdomains-scraper")
    print(f"{Fore.GREEN}Автор: {Fore.CYAN}https://t.me/niko13teen\n")
    
    parser = argparse.ArgumentParser(description='Crawl a website and find subdomains in JS files.')
    parser.add_argument('start_url', type=str, help='The URL of the website to crawl (e.g. https://example.com)')
    args = parser.parse_args()

    start_url = args.start_url
    
    print(f"Получение архитектуры ресурса: {start_url}\n")
    sitemap = crawl_website(start_url)

    all_subdomains_in_js = set()

    for url in tqdm(sitemap, desc="Сбор данных:", unit="url"):
        subdomains_in_js = find_subdomains_in_js_and_save(url)
        all_subdomains_in_js.update(subdomains_in_js)

    save_results_to_file(all_subdomains_in_js, sitemap)

    print("\nРезультаты записаны в файл 'results.txt'.")

if __name__ == "__main__":
    main()