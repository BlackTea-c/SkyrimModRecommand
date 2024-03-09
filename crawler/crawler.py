import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv

data_list = []


def scrape_mod_pages(url, num_pages):
    driver = webdriver.Chrome()

    try:
        current_url = url  # 保存当前URL

        for page in range(1, num_pages + 1):
            driver.get(current_url)  # 使用保存的URL

            # 确认当前页面是否是目标页面
            confirmation = input("确认当前页面是否是你想爬取的页面？(y/n): ")
            if confirmation.lower() != 'y':
                break

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'mod-tile')))

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            mod_tiles = soup.find_all('li', class_='mod-tile')

            for mod_tile in mod_tiles:
                title = mod_tile.find('p', class_='tile-name').find('a').text.strip()
                link = mod_tile.find('a', class_='mod-image')['href']
                category = mod_tile.find('div', class_='category').find('a').text.strip()
                img_url = mod_tile.find('div', class_='fore_div_mods').find('img', class_='fore')['src']
                description = mod_tile.find('p', class_='desc').text.strip()

                print(f"Title: {title}")
                print(f"Link: {link}")
                print(f"Description: {description}")
                print(f"Category: {category}")
                print(f"Image URL: {img_url}")
                print("\n")

                data_list.append([title, link, description, category, img_url])

            # 询问用户是否切换到下一页
            next_page = input("是否切换到下一页？(y/n): ")
            if next_page.lower() == 'y':
                current_url = driver.current_url  # 保存当前页面的URL
            else:
                break

    finally:
        driver.quit()


url_to_scrape = 'https://www.nexusmods.com/skyrimspecialedition/mods/'
scrape_mod_pages(url_to_scrape, num_pages=8)

# 将数据写入CSV文件
with open('mod_data1.csv', 'w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Title', 'Link', 'Description', 'Category', 'Image URL'])  # 写入表头
    csv_writer.writerows(data_list)
