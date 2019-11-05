# -*- encoding: utf-8 -*-

import datetime
import re

import bs4
import psycopg2
import requests

conn = psycopg2.connect(dbname='d9gqs0c8qluemb', user='rfyglxtwtqlzun',
                        host='ec2-174-129-231-116.compute-1.amazonaws.com',
                        password='38ae72b269ce6d2ed66524d4ece1fb3ba412f380c22128f27a7f3ee780465524')
cursor = conn.cursor()

urls = {'realt.by': 'https://realt.by/sale/flats/zhodino/?page=',
        'domovita.by': 'https://domovita.by/zhodino/flats/sale?page='}


def page_count(urls):
    counts = {}
    for name, url in urls.items():
        page_url = url + "0"
        s = requests.get(page_url)
        b = bs4.BeautifulSoup(s.text, "html.parser")
        if name == 'realt.by':
            count = b.find('div', {'class': 'uni-paging'}).findAll("a")[-1].text
        elif name == 'domovita.by':
            item = b.find('div', {'class': 'col-sm-12 fs-12 lh-30 findcount'}).text
            count = int(re.search(r'\d+', item).group(0)) // 20 + 1
        counts[name] = count
    print(counts)
    # {'realt.by': '8', 'domovita.by': 5}
    return counts


counts = page_count(urls)


def parser(url, count):
    if name == 'realt.by':
        page_range = range(0, count)
    elif name == 'domovita.by':
        page_range = range(1, count + 1)

    for x in page_range:
        print(x, url + str(x))
        s = requests.get(url + str(x))
        b = bs4.BeautifulSoup(s.text, "lxml")
        if name == 'realt.by':
            order_list = b.findAll('div', {'class': 'bd-item'})
        elif name == 'domovita.by':
            order_list = b.findAll('div', {'class': 'found_item p-0 clearfix d_flex align-description OFlatsSale '})

        for order in order_list:
            # site
            sitename = re.search(r'\w+\.\w+', url).group(0)

            # code
            order_code = get_code(order)
            cursor.execute("SELECT * from public.\"apartaments\" WHERE order_code = %s;", (order_code,))
            rows = cursor.fetchall()

            if not rows:
                # name
                order_name = get_name(order)
                print('Name: ', order_name)

                # link
                order_link = get_link(order)
                print('Link: ', order_link)

                # current time
                currentdatetime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
                print('Time now: ', currentdatetime)

                # update
                order_update = get_updated(order)
                print('Updated: ', order_update)

                # who
                order_who = get_who(order)
                print("Who: " + order_who)

                # number
                order_numbers, order_number_name = get_numbers(order)
                print('Numbers: ' + order_numbers)
                print('Numbers_name: ' + order_number_name)

                # price
                order_all = get_order_all(order)
                print('Price: ' + order_all)

                # price by m2
                order_by_m2 = get_order_by_m2(order)
                print('Price by m2: ' + order_by_m2)

                # small where
                region, sity = get_region(order, order_name)
                print("Region: ", region)
                print("Sity: ", sity)

                # about
                small_about = get_about(order)
                print("About: ", small_about)

                # flour
                flour = parse_about(order)
                print("Flour: ", flour)

                params = (sitename, order_name, order_link, order_all, order_by_m2, order_code, small_about, flour,
                          region, sity, order_update, currentdatetime)
                cursor.execute(
                    "INSERT INTO public.\"apartaments\"(sitename, order_name, order_link, order_all, order_by_m2, "
                    "order_code, small_about, flour, region, sity, order_update, currentdatetime) "
                    "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", params)

        conn.commit()


def get_about(order):
    if name == 'realt.by':
        order_about = order.find('div', {'class': 'bd-item-right-center'})
        small_about = order_about.find_all("p")[-1].get_text()
    elif name == 'domovita.by':
        small_about = re.sub(r'^\s', '', order.find('div', {'class': 'text-block'}).text)
    return small_about


def get_region(order, order_name):
    if name == 'realt.by':
        order_about = order.find('div', {'class': 'bd-item-right-center'})
        small_where = order_about.find('p').text
        region = small_where.split(', ')[0]
        sity = small_where.split(', ')[1]
    elif name == 'domovita.by':
        sity = re.sub(r',', '', re.findall(r'\S+', order_name)[2])
        region = "None"
    return region, sity


def get_order_by_m2(order):
    if name == 'realt.by':
        order_price = order.find('span', {'class': 'price-byr'}).text
        order_by_m2 = re.search(r'\d+\s+\d+\s+руб/кв.м', order_price)
        if not order_by_m2:
            order_by_m2 = re.search(r'\d+\s+руб/кв.м', order_price)
        if order_by_m2 is not None:
            order_by_m2 = re.sub(r'\s+', '', re.sub(r'\s+руб/кв.м', '', order_by_m2.group(0)))
        else:
            order_by_m2 = "None"
    elif name == 'domovita.by':
        order_by_m2 = order.find('div', {'class': 'col-md-4 text-right'}).find_all('div', {'class': 'gr fs-14'})[-1]
        order_by_m2 = re.search(r'\d+\s+\d+|\d+', order_by_m2.text)
        order_by_m2 = re.sub(r'\s+', '', order_by_m2.group(0))
    return order_by_m2


def get_order_all(order):
    if name == 'realt.by':
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
    elif name == 'domovita.by':
        order_all = order.find('div', {'class': 'price dropdown-toggle green'})
        if not order_all:
            order_all = order.find('div', {'class': 'price dropdown-toggle '})
        order_all = re.sub(r'\s+', '', re.search(r'\d+\s+\d+', order_all.text).group(0))
    return order_all


def get_numbers(order):
    if name == 'realt.by':
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
    elif name == 'domovita.by':
        order_numbers = 'None'
        order_number_name = 'None'
    return order_numbers, order_number_name


def get_who(order):
    if name == 'realt.by':
        order_who = order.find('p', {'class': 'f12'})
        if order_who is not None:
            order_who = order_who.text
        else:
            order_who = "None"
    elif name == 'domovita.by':
        order_who = "None"
    return order_who


def get_updated(order):
    if name == 'realt.by':
        order_update = order.find('p', {'class': 'fl f11 grey'}).text
    elif name == 'domovita.by':
        order_update = order.find('div', {'class': 'date'}).text
    order_update = re.search(r'\d+\.\d+\.\d+', order_update).group(0)
    order_update = datetime.datetime.strftime(datetime.datetime.strptime(order_update, '%d.%m.%Y'), '%Y-%m-%d')
    return order_update


def get_link(order):
    if name == 'realt.by':
        order_link = order.find('div', {'class': 'title'}).find('a').get('href')
    elif name == 'domovita.by':
        order_link = order.find('a', {'class': 'mb-5'}).get('href')
    return order_link


def parse_about(order):
    if name == 'realt.by':
        order_about = order.find('div', {'class': 'bd-item-right-center'})
        small_about = order_about.find_all("p")[-1].get_text()
        flour = re.search(r'^\d+/\d+', small_about)
        if flour:
            flour = flour.group(0)
        else:
            flour = "None"
    elif name == 'domovita.by':
        flour = order.find('div', {'class': 'autopaddings mb-5'}).find_all('span')[1].text
        flour = re.sub(r'\s+этаж из+\s', "/", flour)
    return flour


def get_code(order):
    if name == 'realt.by':
        order_code = re.sub(r'Код: ', '', order.find('p', {'class': 'fr f11 grey'}).text)
    elif name == 'domovita.by':
        order_code = order.get('data-key')
    return order_code


def get_name(order):
    if name == 'realt.by':
        order_name = order.find('div', {'class': 'title'}).find('a').text
    elif name == 'domovita.by':
        order_name = order.find('a', {'class': 'mb-5'}).text
    return order_name


for name, url in urls.items():
    count = int(counts[name])
    parser(url, count)
