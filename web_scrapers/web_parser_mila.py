import requests
from bs4 import BeautifulSoup as BS
import pandas as pd

catalog_url = "https://mila.by/catalog/"
response = requests.get(catalog_url)
soup = BS(response.content, "html.parser")

data = {'name': [], 'price': [], 'category': []}
categories = []
category = str
product_category=str
product_data = pd.DataFrame(data)
unique_products = set()

main_categories = soup.find_all('p', class_='name')

for main_category in main_categories[2:]:
    i = 0
    main_category_link = main_category.find('a')
    main_category_url = main_category_link['href']
    if main_category_url.startswith('/'):
        main_category_url = 'https://mila.by' + main_category_url
    print(main_category.text)

    page = 1
    has_more = True
    while has_more:
        paginated_url = f"{main_category_url}?page={page}"
        main_category_response = requests.get(paginated_url, timeout=30)
        main_category_soup = BS(main_category_response.content, 'html.parser')

        product_links = main_category_soup.find_all('a', class_='offer-link')

        if not product_links:
            break

        for product_link in product_links:
            product_link_url = product_link.get('href')
            if product_link_url.startswith('/'):
                product_link_url = 'https://mila.by' + product_link_url

            product_response = requests.get(product_link_url, timeout=30)
            if product_response.status_code != 200:
                print(f"Ошибка {product_response.status_code} при доступе к {product_link_url}")
                continue

            product_soup = BS(product_response.content, 'html.parser')
            title_elem = product_soup.find('h1')
            name = title_elem.get_text(strip=True) if title_elem else 'Название отсутствует'

            if product_soup.find('div', class_='price-old'):
                price = product_soup.find('div', class_='price-old')
            else:
                price = product_soup.find('div', class_='price')

            price = price.text.strip() if price else 'Цена отсутствует'
            if price.isdigit():
                price = price[:-2] + '.' + price[-2:]

            category = product_soup.find('div', class_="limited-container breadcrumb-wrapper").text
            categories = category.split("—")
            product_category = categories[3]
            ##print(category_product)
            product_tuple = (name, price, product_category)

            if product_tuple in unique_products:
                continue

            unique_products.add(product_tuple)
            i += 1

            new_row = pd.DataFrame({'name': [name], 'price': [price], 'category': [product_category]})
            product_data = pd.concat([product_data, new_row], ignore_index=True)
            print(name, price, product_category, i)

        load_more_button = main_category_soup.find('a', class_='button pink')
        if load_more_button and 'href' in load_more_button.attrs:
            page += 1
        else:
            has_more = False

product_data.to_csv("products.csv", index=False)
