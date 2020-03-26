import json
import time
from pprint import pprint

import bibtexparser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import scholarly

_LIBRARY = 'https://scholar.google.com/scholar?scilib=1&hl=en&as_sdt=0,5'
_CITES = 'https://scholar.google.com/scholar?cites={0}&as_sdt=2005&sciodt=0,5&hl=en'

_current_page = 0


def get_next_pub(query):
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
    abstract = abstract.replace(u'\xa0', '')
    citedby = pub.citedby
    authors = bib['author']
    publisher = 'none'
    if 'publisher' in bib:
        publisher = bib['publisher']
    year = -1
    if 'year' in bib:
        year = int(bib['year'])
    url = bib['url']
    info = {
        'title': title,
        'abstract': abstract,
        'citedby': citedby,
        'authors': authors,
        'publisher': publisher,
        'year': year,
        'url': url
    }

    if hasattr(pub, 'cities'):
        info['cities'] = pub.cities

    return info


def close_window(driver):
    driver.execute_script("window.close()")
    global _current_page
    _current_page = _current_page - 1
    driver.switch_to.window(driver.window_handles[_current_page])
    time.sleep(1)


def next_page(driver):
    try:
        navigation = driver.find_element_by_id('gs_n')
    except NoSuchElementException:
        return False

    tds = navigation.find_elements_by_tag_name('td')
    td = tds[len(tds) - 1]
    try:
        a = td.find_element_by_tag_name('a')
    except NoSuchElementException:
        return False
    td.click()
    return True


def save_in_file(info):
    with open('C:\\scholar.json', 'w') as f:
        json.dump(info, f, indent=4)


def get_all_pubs(soup):
    search_query = scholarly.search_scholar_soup(soup)
    pubs = []
    pub = get_next_pub(search_query)
    i = 0
    while not (pub is None):
        pubs.append(pub)
        print('Обрабатываем ' + str(i + 1) + ' публикацию...')
        i += 1
        pub = get_next_pub(search_query)

    if i == 0:
        print('Похоже Google заблокировал нас... Ну или таких публикаций не существует')
    else:
        print('Получено публикаций: ' + str(i))

    return pubs


def add_pubs_in_lib(driver):
    rows = driver.find_elements_by_class_name('gs_or')
    rows.reverse()
    for row in rows:
        databox = row.find_element_by_class_name('gs_ri')
        lowerlinks = databox.find_element_by_class_name('gs_fl')
        star = lowerlinks.find_element_by_class_name('gs_or_sav')
        time.sleep(0.5)
        star.click()
        if not check_available_star(driver):
            driver.delete_all_cookies()
            star.click()
            login(driver)
            star.click()


def get_pubs_from_lib(driver):
    time.sleep(1)
    driver.execute_script("window.open('" + _LIBRARY + "','_blank');")
    global _current_page
    _current_page = _current_page + 1
    driver.switch_to.window(driver.window_handles[_current_page])

    check_captcha(driver)

    html = driver.page_source
    html = html.replace(u'\xa0', ' ')
    soup = BeautifulSoup(html, 'html.parser')
    pubs = get_all_pubs(soup)

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

    driver.back()
    delete_pubs_in_lib(driver)

    return pubs


def get_cites_pubs_on_pub(driver, pub):
    driver.get(_CITES.format(pub.id_scholarcitedby))
    check_captcha(driver)
    main_pubs = []
    unchecked_citations(driver)
    while True:
        add_pubs_in_lib(driver)
        pubs = get_pubs_from_lib(driver)
        main_pubs.extend(pubs)
        close_window(driver)
        if not next_page(driver):
            break
    return main_pubs


def get_pubs_with_cities(driver):
    pubs = get_pubs_from_lib(driver)  # есть главные публикации, нужно получить статьи, которые их цитируют
    infos = []
    for pub in pubs:
        if pub.citedby != 0:
            pub_cities = get_cites_pubs_on_pub(driver, pub)
            cities = []
            for citi in pub_cities:
                info_citi = get_all_info_from_pub(citi)
                cities.append(info_citi)
            pub.cities = cities
        info = get_all_info_from_pub(pub)
        infos.append(info)
        save_in_file(infos)


def delete_pubs_in_lib(driver):
    check_captcha(driver)
    menu = driver.find_element_by_id('gs_ab_md')
    checkbox = menu.find_element_by_class_name('gs_in_cbj')
    checkbox.click()

    delete = menu.find_element_by_id('gs_res_ab_del')
    delete.click()
    check_captcha(driver)


def unchecked_citations(driver):
    filters = driver.find_element_by_id('gs_bdy_sb_in')
    ul = filters.find_elements_by_class_name('gs_bdy_sb_sec')[2]
    li = ul.find_elements_by_tag_name('li')[1]
    a = li.find_element_by_tag_name('a')
    a.click()


def check_available_star(driver):
    span = driver.find_element_by_id('gs_alrt_m')
    print(span.text)
    return len(span.text) == 0


def check_captcha(driver):
    try:
        WebDriverWait(driver, 3000).until(
            EC.presence_of_element_located((By.ID, "gs_res_ccl"))
        )
    finally:
        pass


def login(driver):
    div = driver.find_element_by_class_name('WEQkZc')
    li = div.find_elements_by_tag_name('li')
    print(len(li))
    li[0].click()

    time.sleep(3)

    div = driver.find_element_by_class_name('Xb9hP')
    input = div.find_element_by_tag_name('input')
    input.send_keys('Sasha1999sas!')

    time.sleep(3)

    button = driver.find_element_by_class_name('qhFLie').find_element_by_tag_name('div')
    button.click()


if __name__ == '__main__':
    print('Начинаем работу')
    # query = input("Введите запрос: ")  # тут мы пишем наш запрос
    query = 'Perception of physical stability and center of mass of 3D objects'
    print("Запрос принят. Начинаем обработку")

    options = webdriver.ChromeOptions()
    options.add_argument('user-data-dir=C:\\Users\\ScRiB\\AppData\\Local\\Google\\Chrome\\User Data 2')
    options.add_argument("--profile-directory=Profile 4")
    driver = webdriver.Chrome(executable_path=r'C:\\Users\\ScRiB\\Desktop\\Firefox\\chromedriver.exe', options=options)

    url = "https://scholar.google.com/scholar?lookup=0&hl=en&q=" + str(query)

    driver.get(url)

    check_captcha(driver)

    unchecked_citations(driver)

    try:
        add_pubs_in_lib(driver)
        get_pubs_with_cities(driver)
    except NoSuchElementException:
        print('Что-то пошло не так...')

    print('Программа завершила работу')
    # driver.quit()
