"""utils.py"""
import time

from playsound import playsound
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_next_pub(query):
    """Получаем следующий объект из генератора"""
    try:
        elem = next(query)
    except StopIteration:
        return None
    return elem


def check_available_star(driver):
    """Проверяем, есть ли возможность добавить публикацию в библиотеку"""
    span = driver.find_element_by_id('gs_alrt_m')
    return span.text != "The system can't perform the operation now. Try again later."


def set_page_in_20(driver):
    """Устанавливаем количество отображаемых страниц в 20 штук"""
    burger = driver.find_element_by_id('gs_hdr_mnu')
    burger.click()

    div = driver.find_element_by_id('gs_hdr_drw_in')
    div = div.find_elements_by_tag_name('div')[1]
    div = div.find_elements_by_tag_name('div')[3]
    a = div.find_element_by_tag_name('a')
    a.click()

    span = driver.find_element_by_id('gs_num-bl')
    if span.text != '20':
        button = driver.find_element_by_id('gs_num-b')
        button.click()

        div = driver.find_element_by_id('gs_num-d')
        div = div.find_element_by_tag_name('div')
        a = div.find_elements_by_tag_name('a')[1]
        a.click()

    save_btn = driver.find_element_by_id('gs_settings_buttons').find_elements_by_tag_name('button')[0]
    save_btn.click()


def unchecked_citations(driver):
    """Убираем галочку для показа цитат"""
    filters = driver.find_element_by_id('gs_bdy_sb_in')
    ul = filters.find_elements_by_class_name('gs_bdy_sb_sec')[2]
    li = ul.find_elements_by_tag_name('li')[1]
    a = li.find_element_by_tag_name('a')
    a.click()


def get_driver(path_to_driver, path_to_profile, profile):
    options = webdriver.ChromeOptions()
    options.add_argument('user-data-dir=' + path_to_profile)
    options.add_argument("--profile-directory=" + profile)
    options.add_argument("--start-maximized")
    # options.add_argument("--proxy-server=85.208.84.138:52332")

    driver = webdriver.Chrome(executable_path=r'{0}'.format(path_to_driver), options=options)
    return driver


def login(driver, url, email, password, open_window, close_window):
    """Входим в аккаунт после очистки куки"""
    open_window(driver, "some")
    driver.get("chrome://settings/clearBrowserData")
    time.sleep(2)
    driver.find_element(By.XPATH, "//settings-ui").send_keys(Keys.ENTER)

    time.sleep(3)

    driver.get(url)

    driver.find_element_by_id('gs_hdr_act_s').click()

    time.sleep(1)

    driver.find_element_by_id('identifierId').send_keys(email)
    driver.find_element_by_id('identifierNext').click()

    time.sleep(3)

    div = driver.find_element_by_class_name('Xb9hP')
    input = div.find_element_by_tag_name('input')
    input.send_keys(password)

    time.sleep(1)

    button = driver.find_element_by_class_name('qhFLie').find_element_by_tag_name('div')
    button.click()

    time.sleep(3)

    close_window(driver)


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
