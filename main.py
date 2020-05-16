import time

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException

import saver
import scholarly
import utils

_MAIN = "https://scholar.google.com/scholar?&lookup=0&hl=en&q={0}"
_LIBRARY = 'https://scholar.google.com/scholar?scilib=1&hl=en&as_sdt=0,5'
_CITES = 'https://scholar.google.com/scholar?cites={0}&as_sdt=2005&sciodt=0,5&hl=en'

_EMAIL = 'swehgadsfgae@gmail.com'
_PASSWORD = 'Sasha1999sas!'

_PATH_TO_PROFILE = 'C:\\Users\\ScRiB\\AppData\\Local\\Google\\Chrome\\User Data 3'
_PROFILE = 'Profile 5'
_PATH_TO_DRIVER = 'C:\\Users\\ScRiB\\Desktop\\GChrome\\chromedriver.exe'

_RESULT_FILE = 'results\\result.json'
_CONTINUE_FILE = 'results\\continue.json'

_current_page = 0
_CONTINUE_INFO = {
    "query": "",  # последний запрос
    "main_page": 0,  # номер страницы главных публикаций
    "cities_index": 0,  # индекс публикации в списке главных публикаций
    "citations_page": 1,  # номер страницы цитируемых публикаций
    "last_index_in_result": 1 # следующий индекс в файле result
}


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
    utils.login(driver, url, _EMAIL, _PASSWORD, open_window, close_window)
    time.sleep(2)
    driver.refresh()
    utils.check_captcha(driver)

    utils.set_page_in_20(driver)

    utils.check_captcha(driver)

    open_window(driver, _LIBRARY)
    utils.check_captcha(driver)

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
        time.sleep(0.4)
        star.click()
        if not utils.check_available_star(driver):
            refresh_library(driver)
            break


def get_pubs_from_lib(driver):
    """Получаем все публикации из библиотеки"""
    open_window(driver, _LIBRARY)

    utils.check_captcha(driver)

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

    if utils.check_captcha(driver):
        time.sleep(5)
        driver.get(_LIBRARY)
        delete_pubs_in_lib(driver)

    return pubs


def get_cites_pubs_on_pub(driver, pub, main_index):
    """Получаем все публикации, в которых цитируется указанная"""
    driver.get(_CITES.format(pub.id_scholarcitedby))
    utils.check_captcha(driver)
    utils.unchecked_citations(driver)

    for z in range(1, _CONTINUE_INFO['citations_page']):
        time.sleep(0.5)
        if not utils.next_page(driver):
            print('Такой страницы с публикациями нет')
            break

    i = _CONTINUE_INFO['citations_page'] - 1
    while True:
        i = i + 1
        _CONTINUE_INFO['citations_page'] = i
        _CONTINUE_INFO['last_index_in_result'] = saver.get_last_index()
        saver.save_in_file(_CONTINUE_INFO, _CONTINUE_FILE)
        add_pubs_in_lib(driver)
        pubs = get_pubs_from_lib(driver)
        close_window(driver)
        for citi in pubs:
            saver.save(_RESULT_FILE, citi, main_index)
        if not utils.next_page(driver) or i > 9:
            break


def get_pubs_with_cities(driver):
    """Соединяем публикации с их цитирующими публикацями"""
    indexes = []
    pubs = get_pubs_from_lib(driver)
    for pub in pubs:
        indexes.append(saver.save(_RESULT_FILE, pub))

    _CONTINUE_INFO['last_index_in_result'] = saver.get_last_index()
    saver.save_in_file(_CONTINUE_INFO, _CONTINUE_FILE)

    for p in range(_CONTINUE_INFO['cities_index'], len(indexes)):
        _CONTINUE_INFO['cities_index'] = p
        saver.save_in_file(_CONTINUE_INFO, _CONTINUE_FILE)
        if pubs[p].citedby != 0:
            get_cites_pubs_on_pub(driver, pubs[p], indexes[p])
            _CONTINUE_INFO['citations_page'] = 1
    _CONTINUE_INFO['cities_index'] = 0


def delete_pubs_in_lib(driver):
    """Удаляем публикации из библиотеки"""
    try:
        if utils.next_page(driver):
            utils.check_captcha(driver)
            delete_pubs_in_lib(driver)
            driver.get(_LIBRARY)
        menu = driver.find_element_by_id('gs_ab_md')
        checkbox = menu.find_element_by_class_name('gs_in_cbj')
        checkbox.click()

        delete = menu.find_element_by_id('gs_res_ab_del')
        delete.click()
        if utils.check_captcha(driver):
            driver.get(_LIBRARY)
            delete_pubs_in_lib(driver)
        return True
    except NoSuchElementException:
        close_window(driver)
        return False


def clear_lib(driver):
    open_window(driver, _LIBRARY)
    if delete_pubs_in_lib(driver):
        close_window(driver)


if __name__ == '__main__':
    driver = None
    is_continue = -1
    while is_continue != 0 and is_continue != 1:
        try:
            is_continue = int(input("Начать работу заново(0) или продолжить(1): "))
        except Exception:
            is_continue = -1

        if is_continue != 0 and is_continue != 1:
            print('Введите корректный режим работы (0 или 1)')
            continue
        page = 1

        if is_continue == 0:
            query = input("Введите запрос: ")
            _CONTINUE_INFO['query'] = query
            saver.init_file(_RESULT_FILE)
        else:
            file = None
            try:
                file = saver.read_file(_CONTINUE_FILE)
            except FileNotFoundError:
                print('Файл с информацией о продолжении не найден')
                exit(-1)
            if 'query' not in file \
                    or 'main_page' not in file \
                    or 'cities_index' not in file \
                    or 'citations_page' not in file \
                    or 'last_index_in_result' not in file:
                print('В файле с информацией о продолжении недостаточно данных')
                exit(-2)
            _CONTINUE_INFO = file
            query = _CONTINUE_INFO['query']
            page = _CONTINUE_INFO['main_page']
            saver.set_index(_CONTINUE_INFO['last_index_in_result'])
            print('Последний запрос: ', query)

        print("Запрос принят. Начинаем обработку")

        url = _MAIN.format(str(query))
        driver = utils.get_driver(_PATH_TO_DRIVER, _PATH_TO_PROFILE, _PROFILE)
        driver.get(url)

        try:
            driver.find_element_by_id('gs_hdr_act_s')
            utils.login(driver, url, _EMAIL, _PASSWORD, open_window, close_window)
        except NoSuchElementException:
            pass

        utils.check_captcha(driver)

        utils.set_page_in_20(driver)
        utils.check_captcha(driver)
        clear_lib(driver)

        utils.unchecked_citations(driver)

        if is_continue == 1:
            for i in range(1, page):
                time.sleep(0.5)
                if not utils.next_page(driver):
                    print('Такой страницы с главными публикациями нет')
                    break

        i = page - 1
        while True:
            i = i + 1
            _CONTINUE_INFO['main_page'] = i
            saver.save_in_file(_CONTINUE_INFO, _CONTINUE_FILE)
            add_pubs_in_lib(driver)
            get_pubs_with_cities(driver)
            close_window(driver)
            if not utils.next_page(driver):
                break

        driver.quit()
    print('Программа завершила работу')
