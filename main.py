import time
from pprint import pprint

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from playsound import playsound

import scholarly
import utils

_MAIN = "https://scholar.google.com/scholar?lookup=0&hl=en&q={0}"
_LIBRARY = 'https://scholar.google.com/scholar?scilib=1&hl=en&as_sdt=0,5'
_CITES = 'https://scholar.google.com/scholar?cites={0}&as_sdt=2005&sciodt=0,5&hl=en'

_EMAIL = 'swehgadsfgae@gmail.com'
_PASSWORD = 'Sasha1999sas!'

_PATH_TO_PROFILE = 'C:\\Users\\ScRiB\\AppData\\Local\\Google\\Chrome\\User Data 3'
_PROFILE = 'Profile 5'
_PATH_TO_DRIVER = 'C:\\Users\\ScRiB\\Desktop\\GChrome\\chromedriver.exe'

_current_page = 0


def get_all_info_from_pub(pub):
    """Получаем из публикации нужную на информацию"""
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


def open_window(driver, page):
    driver.execute_script("window.open('" + page + "','_blank');")
    global _current_page
    _current_page = _current_page + 1
    driver.switch_to.window(driver.window_handles[_current_page])


def close_window(driver):
    """Закрыаем окно браузера и переключаемся на текущую вкладку"""
    driver.execute_script("window.close()")
    global _current_page
    _current_page = _current_page - 1
    driver.switch_to.window(driver.window_handles[_current_page])
    time.sleep(1)


def next_page(driver):
    """Пробуем перейти на следующую страницу публикаций."""
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


def get_all_pubs(soup):
    """Получаем из HTML все публикации на текущей странице"""
    search_query = scholarly.search_scholar_soup(soup)
    pubs = []
    pub = utils.get_next_pub(search_query)
    i = 0
    while not (pub is None):
        pubs.append(pub)
        i += 1
        pub = utils.get_next_pub(search_query)

    if i == 0:
        print('Похоже Google заблокировал нас... Ну или таких публикаций не существует')
    else:
        print('На текущей странице получено {0} публикаций'.format(str(i)))

    return pubs


def refresh_library(driver):
    login(driver)
    time.sleep(2)
    driver.refresh()
    check_captcha(driver)

    utils.set_page_in_20(driver)

    check_captcha(driver)

    open_window(driver, _LIBRARY)
    check_captcha(driver)

    if delete_pubs_in_lib(driver):
        close_window(driver)

    driver.refresh()
    add_pubs_in_lib(driver)


def add_pubs_in_lib(driver):
    """Добавляем все имеющиеся на странице публикации в Личную библиотеку"""
    rows = driver.find_elements_by_class_name('gs_or')
    rows.reverse()
    for row in rows:
        databox = row.find_element_by_class_name('gs_ri')
        lowerlinks = databox.find_element_by_class_name('gs_fl')
        star = lowerlinks.find_element_by_class_name('gs_or_sav')
        time.sleep(0.3)
        star.click()
        if not utils.check_available_star(driver):
            refresh_library(driver)
            break


def get_pubs_from_lib(driver):
    """Получаем все публикации из библиотеки"""
    open_window(driver, _LIBRARY)

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

    bibs = bibtexparser.loads(text, BibTexParser(common_strings=True)).entries
    bibs.reverse()

    for i in range(len(pubs)):
        pubs[i].bib.update(bibs[i])

    driver.back()
    delete_pubs_in_lib(driver)

    if check_captcha(driver):
        time.sleep(5)
        driver.get(_LIBRARY)
        delete_pubs_in_lib(driver)

    return pubs


def get_cites_pubs_on_pub(driver, pub, infos):
    """Получаем все публикации, в которых цитируется указанная"""
    driver.get(_CITES.format(pub.id_scholarcitedby))
    check_captcha(driver)
    main_pubs = []
    cities = []
    utils.unchecked_citations(driver)
    while True:
        add_pubs_in_lib(driver)
        pubs = get_pubs_from_lib(driver)
        close_window(driver)
        for citi in pubs:
            info_citi = get_all_info_from_pub(citi)
            cities.append(info_citi)
        pub.cities = cities
        info = get_all_info_from_pub(pub)
        infos.append(info)
        utils.save_in_file(infos)
        if not next_page(driver):
            break
    return main_pubs


def get_pubs_with_cities(driver):
    """Соединяем публикации с их цитирующими публикацями"""
    pubs = get_pubs_from_lib(driver)  # есть главные публикации, нужно получить статьи, которые их цитируют
    infos = []
    for pub in pubs:
        if pub.citedby != 0:
            get_cites_pubs_on_pub(driver, pub, infos)
            continue
        info = get_all_info_from_pub(pub)
        infos.append(info)
        utils.save_in_file(infos)


def delete_pubs_in_lib(driver):
    """Удаляем публикации из библиотеки"""
    try:
        if next_page(driver):
            check_captcha(driver)
            delete_pubs_in_lib(driver)
            driver.get(_LIBRARY)
        menu = driver.find_element_by_id('gs_ab_md')
        checkbox = menu.find_element_by_class_name('gs_in_cbj')
        checkbox.click()

        delete = menu.find_element_by_id('gs_res_ab_del')
        delete.click()
        return True
    except NoSuchElementException:
        close_window(driver)
        return False


def check_captcha(driver):
    """Проверяем наличие капчи"""
    try:
        captcha = driver.find_element_by_id('recaptcha')
        playsound('Sound_05952.mp3')
        print('Ожидаем ввода капчи')

        try:
            WebDriverWait(driver, 3000).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='//www.google.com/']"))
            )
        finally:
            pass

        return True

    except NoSuchElementException:
        try:
            captcha = driver.find_element_by_id('gs_captcha_ccl')
            playsound('Sound_05952.mp3')
            print('Ожидаем ввода капчи')

            try:
                WebDriverWait(driver, 3000).until(
                    EC.presence_of_element_located((By.ID, "gs_res_ccl"))
                )
            finally:
                pass
            return True

        except NoSuchElementException:
            return False


def login(driver):
    """Входим в аккаунт после очистки куки"""
    open_window(driver, "some")
    driver.get("chrome://settings/clearBrowserData")
    time.sleep(1)
    driver.find_element(By.XPATH, "//settings-ui").send_keys(Keys.ENTER)

    driver.get(url)

    driver.find_element_by_id('gs_hdr_act_s').click()

    time.sleep(2)

    driver.find_element_by_id('identifierId').send_keys(_EMAIL)
    driver.find_element_by_id('identifierNext').click()

    time.sleep(3)

    div = driver.find_element_by_class_name('Xb9hP')
    input = div.find_element_by_tag_name('input')
    input.send_keys(_PASSWORD)

    time.sleep(1)

    button = driver.find_element_by_class_name('qhFLie').find_element_by_tag_name('div')
    button.click()

    time.sleep(3)

    close_window(driver)

    # time.sleep(3)
    # div = driver.find_element_by_class_name('WEQkZc')
    # li = div.find_elements_by_tag_name('li')
    # li[0].click()
    #
    # time.sleep(2)
    #
    # div = driver.find_element_by_class_name('Xb9hP')
    # input = div.find_element_by_tag_name('input')
    # input.send_keys(_PASSWORD)
    #
    # time.sleep(1)
    #
    # button = driver.find_element_by_class_name('qhFLie').find_element_by_tag_name('div')
    # button.click()


def clear_lib(driver):
    open_window(driver, _LIBRARY)
    if delete_pubs_in_lib(driver):
        close_window(driver)


if __name__ == '__main__':
    print('Начинаем работу')
    # query = input("Введите запрос: ")  # тут мы пишем наш запрос
    query = 'Perception of physical stability and center of mass of 3D objects'
    print("Запрос принят. Начинаем обработку")

    options = webdriver.ChromeOptions()
    options.add_argument('user-data-dir=' + _PATH_TO_PROFILE)
    options.add_argument("--profile-directory=" + _PROFILE)

    driver = webdriver.Chrome(executable_path=r'{0}'.format(_PATH_TO_DRIVER), options=options)

    url = _MAIN.format(str(query))

    login(driver)

    driver.get(url)

    check_captcha(driver)

    utils.set_page_in_20(driver)
    check_captcha(driver)
    clear_lib(driver)

    utils.unchecked_citations(driver)

    add_pubs_in_lib(driver)
    get_pubs_with_cities(driver)

    # try:
    #     add_pubs_in_lib(driver)
    #     get_pubs_with_cities(driver)
    # except NoSuchElementException:
    #     print('Что-то пошло не так...')

    print('Программа завершила работу')
    # driver.quit()
