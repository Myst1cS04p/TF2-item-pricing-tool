import requests
from bs4 import BeautifulSoup 
import json
import time
import datetime


bp_api_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxx"
bp_user_token = "xxxxxxxxxxxxxxxxxxxxxxx"
bp_url = "https://backpack.tf/api/classifieds/listings/snapshot"

scrap_pricelist = {}
bp_pricelist = {}

def Log(content):
    print(content)
    f = open("log", "a")
    f.write(content + "\n")
    f.close()


def ProcessBPListings(content, item_name):
        raw_data = content.decode('utf-8')
        data = json.loads(raw_data)
        
        if('listings' in data):
            final_price = data['listings'][0]['price']
            return final_price
        else:
            Log("ERR: could not find 'listings' for: " + item_name)
            return 0
    
# Backpack.tf price checking code
def CheckPriceOnBP(sku):
    sku = str(sku).replace(" ", "%20")
    r = requests.get(bp_url + "?" + "token=" + bp_user_token + "&key=" + bp_api_key + "&sku=" + sku + "&appid=440")
    
    while (r.status_code == 429):
        r = requests.get(bp_url + "?" + "token=" + bp_user_token + "&key=" + bp_api_key + "&sku=" + sku + "&appid=440")
        err_msg = r.content.decode('utf8')
        wait_time = 0        
        for s in err_msg.split():
            if(s.isdigit()):
                wait_time = s
                break
        
        Log("Waiting for " + wait_time)
        
        time.sleep(float(wait_time))
        
        return_val = ProcessBPListings(r.content, sku)
        if(return_val == 0):
            r.status_code = 429
        else:
            return return_val
    
    if(r.status_code == 200):
        final_price = ProcessBPListings(r.content, sku)
        
        if(final_price == 0):
            time.sleep(7)
            final_price = ProcessBPListings(r.content, sku)
        
        return final_price        
    else:
        Log("ERR: Status Code " + str(r.status_code) + " while looking for " + sku)
        return -1

def ProcessScrapPrices():    
    # Open and read the file containing all the scrap.tf prices
    file = open("scrap_prices", "r", encoding="utf8") 
    content = file.read()
    
    # Use beautiful soup to extract relevent information
    soup = BeautifulSoup(content, features="lxml")
    items = soup.find_all(attrs={"data-appid":"440"})
        
    # Loop over each item's details and extract name and price
    for item in items:  
        
        # Extracts the name of each item
        item_name = str(item['data-title']).split(">")
        
        if(len(item_name) > 1):
            item_name = item_name[1].replace("</span", "")
        elif(len(item_name) == 1):
            item_name = item_name[0]
            
        # Extracts the price of each item
        price = str(item['data-content']).split("Costs")[1].replace("<br/>", "").split("<span")[0]
        keys = 0
        if(price.find("key") != -1):
            keys = int(price.split("key")[0])
            price = price.split(', ')[1]
            
        if(price.find("ref")):
            ref = float(price.split("refined")[0])
        
        price = ref + (keys * 57)
        scrap_pricelist.update({item_name : price})


def main():
    f = open("log", "w")
    f.write("Developed by Myst1cS04p\n" + str(datetime.datetime.now()))
    f.close()
    
    
    ProcessScrapPrices()
    
    f = open("profit.csv", "w")
    f.write("Item,Scrap Price Buy,Backpack TF Price,Profit(Scrap -> BP)\n")
    f.close
    
    f = open("profit.csv", "a")
    i = 0
    for item, val in scrap_pricelist.items():
        i += 1
        Log(str(i) + " / " + str(len(scrap_pricelist)))
        
        price = CheckPriceOnBP(item)
        bp_pricelist.update({item : price})
        
        if(price - val > 0):
            profit = price - val
            f.write(item + "," + str(val) + "," + str(price) + "," + str(profit) + "\n")
            
    f.close()

main()