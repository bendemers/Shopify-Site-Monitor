import csv
from discord_hooks import Webhook

with open('old_products.csv', 'r') as t1, open('products.csv', 'r') as t2:
    fileone = t1.readlines()
    filetwo = t2.readlines()

with open('new.csv', 'w') as outFile:
    for line in filetwo:
        if line not in fileone:
            title = line[10:]
            print(title)



    