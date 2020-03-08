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
    with open('C:\\scholar.csv', 'a', newline='') as f:
        w = csv.DictWriter(f, info.keys(), delimiter=';')
        w.writerow(info)


def get_all_pubs(query):
    # scholarly.use_proxy('socks5://5.101.50.175:1080', 'socks5://5.101.50.175:1080')
    search_query = scholarly.search_pubs_query(query)
    pub = get_next(search_query)
    while not (pub is None):
        print('Результат получен. Начинаем обработку...')
        info = get_all_info_from_pub(pub)
        save_in_file(info)
        pub = get_next(search_query)
    print('Все публикации получены')


if __name__ == '__main__':
    get_all_pubs('Perception of physical stability and center of mass of 3D objects')
