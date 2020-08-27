from selenium import webdriver
from requests_html import AsyncHTMLSession
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
import psycopg2

import os
import asyncio
import re


option = webdriver.ChromeOptions()
option.binary_location = os.getenv('GOOGLE_CHROME_BIN')
option.add_argument("--headless")
option.add_argument('--disable-gpu')
option.add_argument('--no-sandbox')

driver = webdriver.Chrome(executable_path=os.getenv('CHROMEDRIVER_PATH'), options=option)
wait_for_tag = lambda tag: WebDriverWait(driver,30).until(lambda x: x.find_element_by_css_selector(tag))

DOMAIN = 'https://emploisfp-psjobs.cfp-psc.gc.ca'
CACHE = []
try:
    driver.get(f'{DOMAIN}/psrs-srfp/applicant/page2440?requestedPage=1&tab=2')
    wait_for_tag('span.pagelinks')

    total_pages = int(re.findall('of (\d+)',driver.page_source)[0])

    for n in range(1,total_pages+1):
        driver.get(f'{DOMAIN}/psrs-srfp/applicant/page2440?requestedPage={n}&tab=2')
        #wait_for_tag('span.pagelinks')

        soup = BeautifulSoup(driver.page_source,'html.parser')
        results = soup.select('li.searchResult')

        for row in results:
            x = row.select_one('a')
            url,title = x.attrs.get('href'), x.text
            date,dept,*loc = list(row.select_one('div.tableCell').stripped_strings)

            CACHE.append({'url': f'{DOMAIN}{url}',
                          'title': title,
                          'closing': date.replace('Closing date: ',''),
                          'department': dept.split(' - ')[0].strip(),
                          'location': ','.join(loc)})
                              
except Exception as e:
    print(e)
        
finally:
    driver.quit()


async def scrape(s,d):
    try:
        url = d.get('url')
        r = await s.get(url)
        text = r.html.find('body',first=True).text
        test = "The job opportunity you have selected requires the Public Service Commission (PSC) to transfer you to the hiring organization's Web site or a service provider Web site they have selected to advertise this process."
        if test in text:
            anchor = r.html.find('main.container > p > a', first=True)
            url = anchor.attrs.get('href')
            r = await s.get(url)
            text = r.html.find('body',first=True).text
    except Exception as e:
        text = ''
    finally:
        d['url'] = url
        d['text'] = text
    return d


async def main():
    
    s = AsyncHTMLSession()
    tasks = (scrape(s,d) for d in CACHE)
    return await asyncio.gather(*tasks)

        
asyncio.run(main())


with sqlite3.connect('gcjobs.db') as conn:
    c = conn.cursor()
    try:
        c.execute('drop table job')
    except:
        pass
    c.execute('create table if not exists job (url text, title text, closing text, department text, location text, contents text)')
    c.executemany('insert into job values (?,?,?,?,?,?)', (tuple(d.values()) for d in CACHE))
    conn.commit()
