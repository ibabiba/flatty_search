# -*- encoding: utf-8 -*-

import psycopg2
import requests
import re
import bs4
import lxml

conn = psycopg2.connect(dbname='d9gqs0c8qluemb', user='rfyglxtwtqlzun',
                        host='ec2-174-129-231-116.compute-1.amazonaws.com',
                        password='38ae72b269ce6d2ed66524d4ece1fb3ba412f380c22128f27a7f3ee780465524')

cursor = conn.cursor()

count = 0
pagetempcount = 0
url = 'https://realt.by/sale/flats/?page='


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

        # results = []

        s = requests.get(url + str(x))
        b = bs4.BeautifulSoup(s.text, "lxml")
        order_list = b.findAll('div', {'class': 'bd-item'})

        for order in order_list:

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
                order_numbers = re.findall(r'\+\d+\s\d+\s\d+\-\d+\-\d+', order_number)
                order_numbers = ', '.join([str(x) for x in order_numbers])
                order_number_name = re.search(r'\D+$', order_number)
                if order_number_name is not None:
                    order_number_name = re.sub(r'\,\s+', '', order_number_name.group(0))
                else:
                    order_number_name = 'None'
            else:
                order_number_name = 'None'


            # format nubers
            if order_numbers is not None:
                order_numbers = re.sub(r'\s', '', re.sub(r'-', '', order_numbers))

            print('Numbers: ' + order_numbers)
            print('Numbers_name: ' + order_number_name)

            params = (order_numbers, str(order_who), order_number_name)

            cursor.execute("INSERT INTO public.\"Agents\"(order_number, order_who, order_number_name) VALUES(%s, %s, "
                           "%s) EXCEPT SELECT * from public.\"Agents\";", (params))
            conn.commit()



parser(url, count)
