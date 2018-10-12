import sys
import csv
import json
import time
import urllib.request
from urllib.error import HTTPError
from optparse import OptionParser
from discord_hooks import Webhook
from shutil import copyfile

collections = ["supreme-0-week"]

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'


def get_page(url, page, collection_handle=None):
    full_url = url
    if collection_handle:
        full_url += '/collections/{}'.format(collection_handle)
    full_url += '/products.json'
    req = urllib.request.Request(
        full_url + '?page={}'.format(page),
        data=None,
        headers={
            'User-Agent': USER_AGENT
        }
    )
    while True:
        try:
            data = urllib.request.urlopen(req).read()
            break
        except HTTPError:
            print('Blocked! Sleeping...')
            time.sleep(180)
            print('Retrying')
        
    products = json.loads(data.decode())['products']
    return products


def get_page_collections(url):
    full_url = url + '/collections.json'
    page = 1
    while True:
        req = urllib.request.Request(
            full_url + '?page={}'.format(page),
            data=None,
            headers={
                'User-Agent': USER_AGENT
            }
        )
        while True:
            try:
                data = urllib.request.urlopen(req).read()
                break
            except HTTPError:
                print('Blocked! Sleeping...')
                time.sleep(180)
                print('Retrying')

        cols = json.loads(data.decode())['collections']
        if not cols:
            break
        for col in cols:
            yield col
        page += 1


def check_shopify(url):
    try:
        get_page(url, 1)
        return True
    except Exception:
        return False


def fix_url(url):
    fixed_url = url.strip()
    if not fixed_url.startswith('http://') and \
       not fixed_url.startswith('https://'):
        fixed_url = 'https://' + fixed_url

    return fixed_url.rstrip('/')


def extract_products_collection(url, col):
    
    page = 1
    products = get_page(url, page, col)
    while products:
        for product in products:
            title = product['title']
            product_type = product['product_type']
            product_url = url + 'products/' + product['handle']
            product_handle = product['handle']

            def get_image(variant_id):
                images = product['images']
                for i in images:
                    k = [str(v) for v in i['variant_ids']]
                    if str(variant_id) in k:
                        return i['src']

                return ''

            for i, variant in enumerate(product['variants']):
                price = variant['price']
                option1_value = variant['option1'] or ''
                option2_value = variant['option2'] or ''
                option3_value = variant['option3'] or ''
                option_value = ' '.join([option1_value, option2_value,
                                         option3_value]).strip()
                sku = variant['sku']
                main_image_src = ''
                if product['images']:
                    main_image_src = product['images'][0]['src']

                image_src = get_image(variant['id']) or main_image_src
                stock = 'Yes'
                if not variant['available']:
                    stock = 'No'

                row = {'sku': sku, 'product_type': product_type,
                       'title': title, 'option_value': option_value,
                       'price': price, 'stock': stock, 'body': str(product['body_html']),
                       'variant_id': product_handle + str(variant['id']),
                       'product_url': product_url, 'image_src': image_src}
                for k in row:
                    row[k] = str(row[k].strip()) if row[k] else ''
                yield row

        page += 1
        products = get_page(url, page, col)





def extract_products(url, path, collections=None):
    
    with open(path, 'w', encoding='utf-8', newline = "") as f:
        writer = csv.writer(f)
        #writer.writerow(['Code', 'Collection', 'Category',
        #                 'Name', 'Variant Name',
        #                'Price', 'In Stock', 'URL', 'Image URL', 'Body'])
        seen_variants = set()
        for col in get_page_collections(url):
            if collections and col['handle'] not in collections:
                continue
            handle = col['handle'] 
            title = col['title']
            for product in extract_products_collection(url, handle):
                variant_id = product['variant_id']
                if variant_id in seen_variants:
                    continue

                seen_variants.add(variant_id)
                writer.writerow([product['title'], product['product_url'],
                                 product['image_src']])

extract_products("https://www.premecopp.com/", 'products.csv', collections)
copyfile("products.csv", "old_prodcuts.csv")

last= ""

while True:
    print("scraping!")
    extract_products("https://www.premecopp.com/", 'products.csv', collections)

    DISCORD_HOOK ="https://discordapp.com/api/webhooks/500094582168748053/OxVosSd6JovhQVVODlOTky4bBjKbNOHPNTETxey5Y7axybY28fbc1Bfth_xKxAMNyVQc"



    with open('old_prodcuts.csv', 'r') as t1, open('products.csv', 'r') as t2:
        fileone = t1.readlines()
        filetwo = t2.readlines()
    for line in filetwo:
        if line not in fileone:
            item = line.split(",")
            if last != item[0]:
                message =("Item: " + item[0] + "\nLink: " + item[1])

                embed = Webhook(DISCORD_HOOK, color = 123123)
                embed.set_desc(message)
                embed.set_thumbnail(item[2])
                embed.post()

                copyfile("products.csv", "old_prodcuts.csv")

                last = item[0]

    time.sleep(15)

