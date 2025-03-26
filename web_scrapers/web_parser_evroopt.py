from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

catalog_url = "https://edostavka.by/categories"
driver.get(catalog_url)
time.sleep(3)

categories = driver.find_elements(By.CSS_SELECTOR, "a.categories_subcategory__link__joHdl")
category_links = [(cat.text, cat.get_attribute("href")) for cat in categories]

product_data = []


def slow_scroll():
    for _ in range(23):  # Повторяем 10 раз
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)  # Отправляем команду "PAGE_DOWN"
        time.sleep(1)


def go_to_next_page():
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Следующая страница']"))
        )
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(3)
        return True
    except:
        return False

def clean_price(price):
    if price:
        cleaned = "".join(char for char in price if char.isdigit() or char == ",")
        return float(cleaned.replace(",", "."))  # Заменяем запятую на точку
    return None


for category_name, category_url in category_links:
    i = 0
    print(f"Парсим категорию: {category_name}")

    page = 1
    has_more = True
    while has_more:
        driver.get(category_url + (f"?page={page}" if page > 1 else ""))
        time.sleep(3)

        slow_scroll()

        products = driver.find_elements(By.CSS_SELECTOR, "div.vertical_product__Q8mUI")

        for product in products:
            try:
                name = product.find_element(By.CSS_SELECTOR, "a.vertical_title__9_9cV").text.strip()
            except:
                name = "Название отсутствует"

            name = name.replace("\xad", "").strip()

            try:
                current_price = product.find_element(By.CSS_SELECTOR, "span.price_main__5jwcE").text.strip()
                current_price = clean_price(current_price)
            except:
                current_price = None

            try:
                old_price = product.find_element(By.CSS_SELECTOR, "span.price_old__XHN68").text.strip()
                old_price = clean_price(old_price)
            except:
                old_price = None

            price = current_price if old_price is None else old_price
            i += 1
            product_data.append([name, price, category_name])
            # print(f"{name} , {price}, {category_name}", i)

        print(f"Всего товаров найдено в категории {category_name}: {i}")


        if go_to_next_page():
            page += 1
            print(f"Переход на страницу {page}...")
        else:
            has_more = False

    print(f"Готово: {category_name}, товаров собрано: {i}")


driver.quit()

df = pd.DataFrame(product_data, columns=["name", "price", "category"])
df.to_csv("products.csv", index=False)

print("Данные сохранены в products.csv")
