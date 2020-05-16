"""saver.py"""

import enum
import json

_index = 1
_FILE_NAME = ''

_DATA = {}


class TypeOfRelations(enum.Enum):
    WROTE = "Wrote"
    REFERS = 'Refers',
    PUBLISHED_BY = 'Published_by',
    QUOTES = 'Quotes',

    def __init__(self, title):
        self.title = title


def save_in_file(info, file_name):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=4, ensure_ascii=False)


def read_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return json.load(f)


def _get_authors_from_pub(pub):
    authors = pub.bib['author']
    temp = []
    for author in authors.split(' and '):
        temp.append(author)
    return temp


def _get_main_info_from_pub(pub):
    bib = pub.bib
    title = bib['title']
    abstract = bib['abstract']
    abstract = abstract.replace(u'\xa0', '')
    cited_by = pub.citedby
    year = -1
    if 'year' in bib:
        year = int(bib['year'])
    info = {
        'index': _index,
        'id': int(pub.id),
        'name': title,
        'description': abstract,
        'dateP': int(year),
        'citations': int(cited_by)
    }

    return info


def _add_pub_in_file(pub):
    info = _get_main_info_from_pub(pub)
    publications = _DATA['Nodes']['Publication']
    for publication in publications:
        if info['id'] == publication['id']:
            return publication['index']
    publications.append(info)
    global _index
    _index = _index + 1
    pub_index = info['index']
    _add_authors_in_file(pub, pub_index)
    _add_source_in_file(pub, pub_index)
    if 'publisher' in pub.bib:
        publisher = str(pub.bib['publisher'])
        _add_publisher(publisher, pub_index)
    return info['index']


def _add_publisher(publisher, pub_index):
    publishers = _DATA['Nodes']['Publishing_house']
    global _index
    publisher = {
        'index': _index,
        'name': publisher
    }
    for publish in publishers:
        if publisher['name'] == publish['name']:
            return publish['index']
    _index = _index + 1
    publishers.append(publisher)
    _add_relation(pub_index, publisher['index'], TypeOfRelations.PUBLISHED_BY)


def _add_author_in_file(author):
    authors_in_file = _DATA['Nodes']['Author']
    for author_in_file in authors_in_file:
        if author_in_file['name'] == author['name']:
            return author_in_file['index']
    authors_in_file.append(author)
    global _index
    _index = _index + 1
    return author['index']


def _add_authors_in_file(pub, pub_index):
    authors = _get_authors_from_pub(pub)
    for author in authors:
        if author == 'others':
            continue
        new_author = {
            'index': _index,
            'name': author,
            'description': 0
        }
        author_index = _add_author_in_file(new_author)
        _add_relation(author_index, pub_index, TypeOfRelations.WROTE)


def _add_source_in_file(pub, pub_index):
    sources = _DATA['Nodes']['Source']
    global _index
    source = {
        'index': _index,
        'name': 0,
        'address': pub.bib['url']
    }
    sources.append(source)
    _index = _index + 1
    _add_relation(source['index'], pub_index, TypeOfRelations.REFERS)


def _add_relation(start, end, type_of_relation):
    relations = _DATA['Relations'][type_of_relation.title]

    rel = {
        'start': start,
        'end': end
    }
    relations.append(rel)


def init_file(file_name):
    if _FILE_NAME == '':
        _init_filename(file_name)
    data = {
        'Nodes': {
            'Publication': [],
            'Author': [],
            'Source': [],
            'Publishing_house': [],
        },
        'Relations': {
            'Wrote': [],
            'Refers': [],
            'Published_by': [],
            'Quotes': [],
        }
    }

    save_in_file(data, _FILE_NAME)


def _init_filename(file_name):
    global _FILE_NAME
    _FILE_NAME = file_name


def _set_data(data):
    global _DATA
    _DATA = data


def get_last_index():
    return _index


def set_index(index):
    global _index
    _index = index


def save(file_name, pub, main_index=None):
    if _FILE_NAME == '':
        _init_filename(file_name)
    _set_data(read_file(_FILE_NAME))
    pub_index = _add_pub_in_file(pub)
    save_in_file(_DATA, _FILE_NAME)
    if main_index is None:
        return pub_index
    _add_relation(main_index, pub_index, TypeOfRelations.QUOTES)
    save_in_file(_DATA, _FILE_NAME)
