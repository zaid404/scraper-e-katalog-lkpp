import csv
import concurrent.futures
import re
import time
import threading
from selenium import webdriver
from bs4 import BeautifulSoup

chromedriver_path = 'C:\\chromedriver_win32\\chromedriver.exe'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')

def extract_data(soup, page_source):
    img_tag = soup.find('img', {'class': 'lazy img img-responsive', 'src': re.compile(r'/katalog/produk/download/gambar/')})
    img_src = img_tag['src'] if img_tag else None

    strContentUnique_match = re.search(r"let strContentUnique = '(.*?)';", page_source)
    strContentUnique = strContentUnique_match.group(1) if strContentUnique_match else None

    strTitle_match = re.search(r"let strTitle = '(.*?)';", page_source)
    strTitle = strTitle_match.group(1) if strTitle_match else None

    price_tag = soup.find('div', {'id': 'detailhargaChange'})
    price = price_tag.get_text().strip() if price_tag else None

    detail_items = soup.find_all('div', {'class': 'detail-item'})
    heading = []
    descriptions = []
    for item in detail_items:
        heading_tag = item.find('div', {'class': 'detail-heading col-md-2'})
        description_tag = item.find('div', {'class': 'detail-description col-md-10'})
        if heading_tag and description_tag:
            heading.append(heading_tag.get_text().strip())
            descriptions.append(description_tag.get_text().strip())

    supplier_tag = soup.find('a', {'class': 'badge'})
    supplier_name = supplier_tag.get_text().strip() if supplier_tag else None

    return img_src, strContentUnique, strTitle, price, supplier_name, descriptions, heading

def scrape_data(url):
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    driver.get(url)
    time.sleep(10)
    page_source = driver.page_source
    driver.quit()
    soup = BeautifulSoup(page_source, 'html.parser')
    return extract_data(soup, page_source)

def scrape_and_save(url):
    img_src, strContentUnique, strTitle, price, supplier_name, descriptions, headings = scrape_data(url)

    base_url = "https://e-katalog.lkpp.go.id/"
    id_ = url.split("/")[-1]
    img_ = f"{base_url}{img_src}"

    data_row = [
        url, strTitle, price, img_, 
        ", ".join([f"{heading}: {description}" for heading, description in zip(headings, descriptions)]),
        supplier_name, strContentUnique
    ]

    with csv_lock:
        csv_writer.writerow(data_row)
        csv_file.flush()

if __name__ == "__main__":
    with open("url.txt", "r") as url_file:
        urls = url_file.readlines()

    csv_lock = threading.Lock()

    with open("output.csv", "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["URL", "Nama Produk", "Harga", "URL Gambar", "Headings and Descriptions", "Supplier", "Produk ID"])


        max_threads = 5
        with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
            futures = [executor.submit(scrape_and_save, url.strip()) for url in urls]

            # Wait for all threads to finish
            for future in concurrent.futures.as_completed(futures):
                pass