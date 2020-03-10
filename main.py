import csv

import scholarly


def get_next(query):
    """Get next object from generator"""
    try:
        elem = next(query)
    except StopIteration:
        return None
    return elem


def get_all_info_from_pub(pub):
    fill_pub = pub.fill()
    bib = fill_pub.bib
    title = bib['title']
    abstract = bib['abstract']
    citedby = fill_pub.citedby
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


def get_all_pubs(query):
    # scholarly.use_proxy('socks5://5.101.50.175:1080', 'socks5://5.101.50.175:1080')
    search_query = scholarly.search_pubs_query(query)
    pub = get_next(search_query)
    i = 0
    while (not (pub is None)) and i < 20:
        print('Обрабатываем ' + str(i + 1) + ' публикацию...')
        info = get_all_info_from_pub(pub)
        save_in_file(info)
        i += 1
        pub = get_next(search_query)

    if (i == 0):
        print('Похоже Google заблокировал нас... Ну или таких публикаций не существует')
    else:
        print('Получено публикаций: ' + str(i+1))


if __name__ == '__main__':
    print('Начинаем работу')
    query = '123'
    print('Ваш запрос: ' + query)
    get_all_pubs(query)
