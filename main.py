import logging
import re
import time
import csv


from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def extract_amount(text):
    pattern = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
    match = re.search(pattern, text)
    if match:
        amount_str = match.group()
        amount_int = int(amount_str.replace('$', '').replace(',', '').split('.')[0])
        return amount_int
    else:
        return 0


def get_count(text):
    pattern = r'\b\d{1,3}(?:,\d{3})*\b'
    match = re.search(pattern, text)
    if match:
        number_str = match.group()
        number_int = int(number_str.replace(',', ''))
        return number_int
    else:
        return 0


def get_mac_chrome_driver():
    options = ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # path_to_driver = ChromeDriverManager().install()
    driver = webdriver.Chrome(options=options)

    return driver


def search_ebay(search, least_price):
    driver = get_mac_chrome_driver()
    wait = WebDriverWait(driver, 10)
    try:
        url = f"https://www.ebay.com/sch/i.html?&_nkw={search}&_sacat=0&&_udlo={least_price}&_ipg=240"
        driver.get(url)
        time.sleep(1)
        sellers = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "s-item__seller-info-text")))
        seller_info = {}
        for each in sellers:
            name = each.text.split("(")[0].strip()
            feedback_counts = each.text.split("(")[1].split(")")[0].strip()
            rating = each.text.split(")")[1].strip()
            if name not in seller_info.keys():
                seller_info[name] = (feedback_counts, rating)
        return True, seller_info
    except Exception as eee:
        logging.exception(eee)
        return False, {}
    finally:
        driver.quit()


def get_ebay_store_info(store, limit, data):
    driver = get_mac_chrome_driver()
    wait = WebDriverWait(driver, 10)

    try:
        url = f"https://www.ebay.com/sch/i.html?&_ssn={store}&_ipg=240"
        driver.get(url)
        time.sleep(1)
        place_holder = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "str-search__input")))
        place_holder = place_holder.get_attribute("placeholder")
        count = get_count(place_holder)
        prices = []
        if count > 0 and count <= limit:
            items_prices = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "s-item__price")))
            for each in items_prices:
                price = extract_amount(each.text)
                prices.append(price)
            prices = list(filter(lambda x: x != 0, prices))
            return {"Seller Name": store, "# of FeedBacks": data[store][0], "Rating": data[store][1],
                    "Max Priced Item": f'{max(prices)}$', "Min Priced Item": f'{min(prices)}$', "Item Quantity": count,
                    "Cumulative Price": f'{sum(prices)}$', "Url": url}
        return None
    except Exception as eee:
        logging.exception(eee)
        return None
    finally:
        driver.quit()


records = []
search = "keysight"
item_limit = 1000
least_price = "5000"

status, data = search_ebay(search, least_price)
if status:
    for each in list(data.keys()):
        result = get_ebay_store_info(each, item_limit, data)
        if result:
            records.append(result)

else:
    logging.error("TECHNICAL ERROR : Try Again.")
# Define the headers
headers = ["Seller Name", "# of FeedBacks", "Rating", "Max Priced Item", "Min Priced Item", "Item Quantity",
           "Cumulative Price", "Url"]


with open('output.csv', 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=headers)

    # Write the header
    writer.writeheader()
    for row in records:
        writer.writerow(row)

print("CSV file created successfully.")