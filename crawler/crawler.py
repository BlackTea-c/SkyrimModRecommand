import os
import sys
import django
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime


data_list=[]
def scrape_mod_pages(url, num_pages):
    driver = webdriver.Chrome()  # 请确保你已经安装了Chrome浏览器，并配置好webdriver

    try:
        for page in range(1, num_pages + 1):
            # 访问当前页
            driver.get(url)

            # 使用WebDriverWait等待页面元素加载完成
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'mod-tile')))

            # 获取网页源代码
            page_source = driver.page_source

            # 使用BeautifulSoup解析HTML
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
                # 将爬取到的数据存储到列表中
                data_list.append([title, link, description, category, img_url])


            # 等待用户手动切换页面,这里我真没找到比较好的方法，大一大二自学的爬虫到大四直接忘了真是艹了
            #（所以说去github之类的网站记录东西真的很有必要= =）
            input("Please switch to the next page manually and press Enter when ready...")
            #设置num_pages，是多少就会循环多少次。


    finally:
        # 关闭浏览器
        driver.quit()

# 调用爬虫程序，例如爬取前5页的内容
url_to_scrape = 'https://www.nexusmods.com/skyrimspecialedition/mods/'
scrape_mod_pages(url_to_scrape, num_pages=5)
# 将数据写入 CSV 文件
import csv
with open('../moiveRe/mod_data.csv', 'w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Title', 'Link', 'Description', 'Category', 'Image URL'])  # 写入表头
    csv_writer.writerows(data_list)