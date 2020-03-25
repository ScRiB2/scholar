import csv

import bibtexparser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import scholarly

_LIBRARY = 'https://scholar.google.com/scholar?scilib=1&hl=en&as_sdt=0,5'


def get_next(query):
    """Получаем следующий объект из генератора"""
    try:
        elem = next(query)
    except StopIteration:
        return None
    return elem


def get_all_info_from_pub(pub):
    bib = pub.bib
    title = bib['title']
    abstract = bib['abstract']
    citedby = pub.citedby
    authors = bib['author']
    publisher = 'none'
    if 'publisher' in bib:
        publisher = bib['publisher']
    year = bib['year']
    url = bib['url']
    return {
        'title': title,
        'abstract': abstract,
        'citedby': citedby,
        'authors': authors,
        'publisher': publisher,
        'year': year,
        'url': url
    }


def save_in_file(info):
    with open('C:\\scholar.csv', 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, info.keys(), delimiter=';')
        w.writerow(info)


def get_all_pubs(soup):
    search_query = scholarly.search_scholar_soup(soup)
    pubs = []
    pub = get_next(search_query)
    i = 0
    while not (pub is None):
        pubs.append(pub)
        print('Обрабатываем ' + str(i + 1) + ' публикацию...')
        i += 1
        pub = get_next(search_query)

    if i == 0:
        print('Похоже Google заблокировал нас... Ну или таких публикаций не существует')
    else:
        print('Получено публикаций: ' + str(i))

    return pubs


def get_star(driver):
    for row in driver.find_elements_by_class_name('gs_or'):
        databox = row.find_element_by_class_name('gs_ri')
        lowerlinks = databox.find_element_by_class_name('gs_fl')
        star = lowerlinks.find_element_by_class_name('gs_or_sav')
        star.click()
        # print(lowerlinks.)


def get_libr(driver):
    # driver.execute_script("window.open('" + _LIBRARY + "','_blank');")
    # driver.switch_to.window(driver.window_handles[1])

    html = driver.page_source
    # html = html.replace(u'\xa0', ' ')
    soup = BeautifulSoup(html, 'html.parser')
    pubs = get_all_pubs(soup)
    print(len(pubs))

    menu = driver.find_element_by_id('gs_ab_md')
    checkbox = menu.find_element_by_class_name('gs_in_cbj')
    checkbox.click()
    downl = driver.find_element_by_id('gs_res_ab_exp-b')
    downl.click()
    bib = driver.find_element_by_id('gs_res_ab_exp-d')
    a = bib.find_elements_by_class_name('gs_md_li')[0]
    a.click()
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.find('pre').contents[0]
    bibs = bibtexparser.loads(text).entries
    bibs.reverse()

    for i in range(len(pubs)):
        pubs[i].bib.update(bibs[i])
        info = get_all_info_from_pub(pubs[i])
        save_in_file(info)


if __name__ == '__main__':
    print('Начинаем работу')
    # query = input("Введите запрос: ")  # тут мы пишем наш запрос
    query = 'Perception of physical stability and center of mass of 3D objects'
    print("Запрос принят. Начинаем обработку")
    options = webdriver.ChromeOptions()
    options.add_argument('user-data-dir=C:\\Users\\ScRiB\\AppData\\Local\\Google\\Chrome\\User Data 2')
    options.add_argument("--profile-directory=Profile 4")
    driver = webdriver.Chrome(executable_path=r'C:\\Users\\ScRiB\\Desktop\\Firefox\\chromedriver.exe', options=options)
    url = "https://scholar.google.com/scholar?scilib=1&hl=en&as_sdt=0,5" + str(query)
    pizzas = driver.get(url)
    try:
        pizza_container = WebDriverWait(driver, 10000).until(
            EC.presence_of_element_located((By.ID, "gs_res_ccl"))
        )
    finally:
        pass
    # get_star(driver)    get_libr(driver)
    print('Программа завершила работу')
    driver.quit()
