# -*- encoding: utf-8 -*-

import psycopg2
import requests
import re
import bs4
import lxml
import datetime

conn = psycopg2.connect(dbname='d9gqs0c8qluemb', user='rfyglxtwtqlzun',
                        host='ec2-174-129-231-116.compute-1.amazonaws.com',
                        password='38ae72b269ce6d2ed66524d4ece1fb3ba412f380c22128f27a7f3ee780465524')

cursor = conn.cursor()
count = 0
pagetempcount = 0
url = 'https://realt.by/sale/flats/zhodino/?page='


def page_count(url, count):
    url = url + str(count)
    s = requests.get(url)
    b = bs4.BeautifulSoup(s.text, "html.parser")

    item = b.find('div', {'class': 'uni-paging'})
    count = item.findAll("a")[-1].text
    print(count)
    return count


count = page_count(url, count)


def parser(url, count):
    for x in range(0, int(count)):
        print(x)
        print(url + str(x))

        s = requests.get(url + str(x))
        b = bs4.BeautifulSoup(s.text, "lxml")
        order_list = b.findAll('div', {'class': 'bd-item'})

        for order in order_list:
            # site
            sitename = re.search(r'\w+\.\w+', url).group(0)

            # code
            order_code = order.find('p', {'class': 'fr f11 grey'}).text
            order_code = re.sub(r'Код: ', '', order_code)

            cursor.execute("SELECT * from public.\"apartaments\" WHERE order_code = %s;", (order_code,))
            rows = cursor.fetchall()
            if not rows:
                # name
                item = order.find('div', {'class': 'title'})
                order_name = item.find('a').text
                print('Name: ' + order_name)

                # link
                order_link = item.find('a').get('href')
                print('Link: ' + order_link)

                # price
                order_price = order.find('span', {'class': 'price-byr'}).text
                order_all = re.match(r'\d+\s+\d+\s+руб,', order_price)
                if not order_all:
                    order_all = re.search(r'\d+\s+руб,', order_price)
                if order_all is not None:
                    order_all = re.sub(r'\s+', '', re.sub(r'\s+руб,', '', order_all.group(0)))
                else:
                    order_all = 'None'
                order_mln = re.match(r'\S+\s+млн\sруб,', order_price)
                if order_mln is not None:
                    order_all = str(float(re.sub(r',', '.', re.sub(r'\s+млн\sруб,', '', order_mln.group(0)))) * 1000000)
                print('Цена: ' + order_all)

                # price by m2
                order_by_m2 = re.search(r'\d+\s+\d+\s+руб/кв.м', order_price)
                if not order_by_m2:
                    order_by_m2 = re.search(r'\d+\s+руб/кв.м', order_price)
                if order_by_m2 is not None:
                    order_by_m2 = re.sub(r'\s+', '', re.sub(r'\s+руб/кв.м', '', order_by_m2.group(0)))
                else:
                    order_by_m2 = "None"
                print('Price by m2: ' + order_by_m2)

                # who
                order_who = order.find('p', {'class': 'f12'})
                if order_who is not None:
                    order_who = order_who.text
                else:
                    order_who = "None"
                print("Who: " + order_who)

                # number
                order_number = order.find('p', {'class': 'mb0'}).get_text()
                if order_number is not None:
                    order_numbers = re.findall(r'\+\d+\s\d+\s\d+-\d+-\d+', order_number)
                    order_numbers = ', '.join([str(x) for x in order_numbers])
                    order_number_name = re.search(r'\D+$', order_number)
                    if order_number_name is not None:
                        order_number_name = re.sub(r',\s+', '', order_number_name.group(0))
                    else:
                        order_number_name = 'None'
                else:
                    order_numbers = 'None'
                    order_number_name = 'None'

                # format nubers
                if order_numbers is not None:
                    order_numbers = re.sub(r'\s|-', '', order_numbers)

                print('Numbers: ' + order_numbers)
                print('Numbers_name: ' + order_number_name)

                # update
                order_update = order.find('p', {'class': 'fl f11 grey'}).text
                order_update = re.sub(r'Обновлено: ', '', order_update)
                order_update = datetime.datetime.strftime(datetime.datetime.strptime(order_update, '%d.%m.%Y'),
                                                          '%Y-%m-%d')
                print(order_update)

                # small where
                order_about = order.find('div', {'class': 'bd-item-right-center'})
                small_where = order_about.find('p').text
                region = small_where.split(', ')[0]
                print(region)
                sity = small_where.split(', ')[1]
                print(sity)

                # about
                small_about = order_about.find_all("p")[-1].get_text()
                print(small_about)

                # flour
                flour = parse_about(small_about)
                print(flour)

                print("")

                # current time
                currentdatetime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
                print(currentdatetime)

                params = (sitename, order_name, order_link, order_all, order_by_m2, order_code, small_about, flour,
                          region, sity, order_update, currentdatetime)
                cursor.execute(
                    "INSERT INTO public.\"apartaments\"(sitename, order_name, order_link, order_all, order_by_m2, "
                    "order_code, small_about, flour, region, sity, order_update, currentdatetime) "
                    "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", params)

        conn.commit()


def parse_about(small_about):
    # flour
    flour = re.search(r'^\d+/\d+', small_about)
    if flour:
        flour = flour.group(0)
    else:
        flour = "None"
    return flour


parser(url, count)
