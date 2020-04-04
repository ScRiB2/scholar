"""utils.py"""

import json


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
    return len(span.text) == 0


def save_in_file(file_name, info):
    with open(file_name, 'w') as f:
        json.dump(info, f, indent=4)


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
