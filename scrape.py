from selenium import webdriver
from requests_html import AsyncHTMLSession
from pyquery import PyQuery
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
import psycopg2

import os
import asyncio
import re

def main():
    option = webdriver.ChromeOptions()
    option.binary_location = os.getenv('GOOGLE_CHROME_BIN')
    option.add_argument("--headless")
    option.add_argument('--disable-gpu')
    option.add_argument('--no-sandbox')

    driver = webdriver.Chrome(executable_path=os.getenv('CHROMEDRIVER_PATH'), options=option)
    wait_for_tag = lambda tag: WebDriverWait(driver,30).until(lambda x: x.find_element_by_css_selector(tag))
    
    USERNAME = os.getenv('GCJOBS_USERNAME')
    PASSWORD = os.getenv('GCJOBS_PASSWORD')
    DOMAIN = 'https://emploisfp-psjobs.cfp-psc.gc.ca'
    CACHE = []
   
    try:
        
        #login
        is_authenticated = False
        try:
            driver.get('https://emploisfp-psjobs.cfp-psc.gc.ca/psrs-srfp/applicant/page1710')
            driver.find_element_by_id('UserNumber').send_keys(USERNAME)
            driver.find_element_by_id('Password').send_keys(PASSWORD)
            driver.find_element_by_css_selector('input[name=LOGIN]').click()
            is_authenticated = True
            
        except Exception as e:
            print(e)
            
        tabs = (1,2) if is_authenticated else (1,)
        for tab in tabs:
            driver.get(f'{DOMAIN}/psrs-srfp/applicant/page2440?requestedPage=1&tab={tab}')
            wait_for_tag('span.pagelinks')
            
            total_pages = int(re.findall('of (\d+)',driver.page_source)[0])

            for n in range(1,total_pages+1):
                driver.get(f'{DOMAIN}/psrs-srfp/applicant/page2440?requestedPage={n}&tab={tab}')
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
                                  'location': ','.join(loc),
                                  'internal': 1 if tab==1 and is_authenticated else 0
                                  }
                                 )

    except Exception as e:
        print(e)

    finally:
        driver.quit()
        print('selenium finished running')


    async def scrape(s,d):
        try:
            url = d.get('url')
            r = await s.get(url)
            text = r.html.find('body',first=True).text
            test = "The job opportunity you have selected requires the Public Service Commission (PSC) to transfer you"
            if test in text:
                anchor = r.html.find('main.container > p > a', first=True)
                url = anchor.attrs.get('href')
                r = await s.get(url)
                pq = PyQuery(r.content)
                pq('script').remove()
                text = pq('body').text()
        except Exception as e:
            text = ''
        finally:
            d['url'] = url
            #possibly redundant adding the title,dept,loc, but ensures it always exists for search
            d['text'] = text + d['title']+d['department']+d['location']
        return d

    async def main():    
        s = AsyncHTMLSession()
        data = {'UserNumber': USERNAME, 'Password': PASSWORD, 'LOGIN': 'Login'}
        await s.post('https://emploisfp-psjobs.cfp-psc.gc.ca/psrs-srfp/applicant/page1710', data=data)
        tasks = (scrape(s,d) for d in CACHE)
        return await asyncio.gather(*tasks)

    asyncio.run(main())
    print('async finished running')

    ROWS,SEEN = [],set()
    for d in CACHE:
        key = (d['url'],d['title'])
        if key not in SEEN:
            ROWS.append(d)
            SEEN.add(key)

    DATABASE_URL = os.getenv('DATABASE_URL')
    if ROWS:
        with psycopg2.connect(DATABASE_URL, sslmode='require') as conn:
            c = conn.cursor()
            c.execute('drop table if exists job;')
            c.execute('CREATE TABLE if not exists job (id serial primary key, url text, title text, closing text, department text, location text, internal smallint, contents text);')
            c.executemany('insert into job(url, title, closing, department, location, internal, contents) values (%s,%s,%s,%s,%s,%s,%s)', (tuple(d.values()) for d in ROWS))
            conn.commit()
        print('data written to postgres')
    else:
        print('no data found to write to postgres')
