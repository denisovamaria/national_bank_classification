import requests
from bs4 import BeautifulSoup as BS
import pandas as pd
import time

catalog_url = 'https://green-dostavka.by/catalog/'
response = requests.get(catalog_url)
time.sleep(2)
soup = BS(response.content, 'html.parser')
data = {'name': [], 'price': [], 'category': []}
product_data = pd.DataFrame(data)

main_categories = soup.find_all(
    'a',
    class_='link_link__1nuz- link_btnWhite__4nruq categories-block_desktop__ZJSa- link_size-s__39Hhf'
)

for main_category in main_categories[4:]:
    main_category_url = main_category['href']
    if main_category_url.startswith('/'):
        main_category_url = 'https://green-dostavka.by' + main_category_url

    main_category_response = requests.get(main_category_url, timeout=10)
    time.sleep(2)
    main_category_soup = BS(main_category_response.content, 'html.parser')

    subcategories = main_category_soup.find_all(
        'a',
        class_='link_link__1nuz- link_btnWhite__4nruq categories-block_desktop__ZJSa- link_size-s__39Hhf'
    )
    title_subcategory = main_category_soup.find_all(
        class_='categories-block_title__2T7E_')
    title_to_href = {}

    for title, subcategory in zip(title_subcategory, subcategories):
        title_text = title.text.strip()
        subcategory_href = subcategory['href']
        if subcategory_href.startswith('/'):
            subcategory_href = 'https://green-dostavka.by' + subcategory_href

        title_to_href[title_text] = subcategory_href
    for title, subcategory_url in title_to_href.items():
        print(title)
        subcategory_response = requests.get(subcategory_url, timeout=10)
        time.sleep(2)
        subcategory_soup = BS(subcategory_response.content, 'html.parser')

        sub_subcategories = subcategory_soup.find_all(
            'a',
            class_='link_link__1nuz- link_btnWhite__4nruq categories-block_desktop__ZJSa- link_size-s__39Hhf'
        )

        for sub_subcategory in sub_subcategories:
            sub_subcategory_url = sub_subcategory['href']
            if sub_subcategory_url.startswith('/'):
                sub_subcategory_url = 'https://green-dostavka.by' + sub_subcategory_url

            offset = 0
            has_more = True

            while has_more:
                paginated_url = f"{sub_subcategory_url}?offset={offset}"
                sub_subcategory_response = requests.get(paginated_url, timeout=30)
                time.sleep(2)  # Задержка в 2 секунды
                sub_subcategory_soup = BS(sub_subcategory_response.content, 'html.parser')

                product_links = sub_subcategory_soup.find_all(
                    class_='link_link__1nuz- product_product__3Gv3O products-list_product__2IR4P')
                for product_link in product_links:
                    product_link_url = product_link.get('href')
                    if product_link_url.startswith('/'):
                        product_link_url = 'https://green-dostavka.by' + product_link_url
                    product_response = requests.get(product_link_url, timeout=10)
                    time.sleep(2)
                    if product_response.status_code != 200:
                        print(f"Ошибка {product_response.status_code} при доступе к {product_link_url}")
                        continue
                    product_soup = BS(product_response.content, 'html.parser')
                    title_elem = product_soup.find(class_='product-modal_productTitle__2Hyco')
                    name = title_elem.text.strip() if title_elem else 'Название отсутствует'
                    if product_soup.find(class_='styles_productOldValue__aBB__'):
                        price = product_soup.find(class_='styles_productOldValue__aBB__')
                    elif product_soup.find(class_='styles_productValue__2SVoW styles_productValueDiscount__j8okF'):
                        continue
                    elif product_soup.find(class_='styles_originalPrice__1kaRX'):
                        price = product_soup.find(class_='styles_originalPrice__1kaRX')
                    else:
                        price = product_soup.find(class_='styles_productValue__2SVoW')
                    price = price.text.strip() if price else 'Цена отсутствует'
                    new_row = pd.DataFrame({'name': [name], 'price': [price], 'category': [title]})
                    product_data = pd.concat([product_data, new_row], ignore_index=True)
                    print(name, price)

                load_more_button = sub_subcategory_soup.find('a',
                                                             class_='link_link__1nuz- link_loadMore__3WO49 link_fluid__1SfuS link_size-m__21Xu5')
                if load_more_button and 'href' in load_more_button.attrs:
                    offset += 100
                else:
                    has_more = False


csv_filename = 'products_dataset_green.csv'
product_data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
print(f"Данные успешно сохранены в файле {csv_filename}")
