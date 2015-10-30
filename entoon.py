import sys
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = 'https://www.onenote.com/api/'
# Specify yr token.
TOKEN = ""
RESERVED_CHARS = '?*\\/:<>|&#''%~'

class Tooner:
    def __init__(self, filename, url=BASE_URL, token=TOKEN):
        self.token = token
        self.url = url
        self.filename = filename
        self.title = self._parse_title(filename)
        self.sections = {}
        self.session = self._create_session()
        self.soup = self._make_soup(filename)
        self.note_template = """
            <?xml version="1.0" encoding="utf-8" ?>
            <html xmlns="http://www.w3.org/1999/xhtml" lang="en-us">
                <head><title>{}</title></head>
                <body>{}</body>
            </html>
        """
        self.notebooks = self._get_notebooks()
        self.notebooks_by_id = self._get_notebooks(by_id=True)

    def notebook_exists(self, notebook):
        return notebook in self.notebooks

    def section_exists(self, section):
        return section in self.sections

    def _create_session(self):
        session = requests.Session()
        session.headers.update({
            'Authorization': TOKEN
        })
        return session

    def _get_notebooks(self, by_id=False):
        method = 'v1.0/me/notes/notebooks?orderby=lastModifiedTime&select=id,name,links&expand=sections&top=50&count=true'
        url = urljoin(self.url, method)
        r = self.session.get(url)
        result = r.json()
        if by_id:
            notebooks = {nb['id']: nb['name'] for nb in result['value']}
        else:
            notebooks = {nb['name']: nb['id'] for nb in result['value']}
        return notebooks

    def _parse_title(self, filepath):
        base = os.path.basename(filepath)
        return base.split('.')[0].title()

    def create_notebook(self, name):
        print("Creating notebook {}".format(name))
        if name in self.notebooks:
            print("{} already exists with ID {}".format(name, self.notebooks[name]))
            return {
                'name': name,
                'id': self.notebooks[name]
            }
        method = 'v1.0/me/notes/notebooks'
        url = urljoin(self.url, method)
        data = {
            "name": name
        }
        r = self.session.post(url, json=data)
        result = r.json()
        self.notebooks['name'] = result['id']
        self.notebooks_by_id[result['id']] = name
        print("Created notebook {} with GUID {}".format(name, result['id']))
        return result

    def create_section(self, notebook_guid, name):
        notebook_name = self.notebooks_by_id[notebook_guid]
        print("Creating section with name {} in Notebook {}".format(name, notebook_name))
        method = 'v1.0/me/notes/notebooks/{}/sections'.format(notebook_guid)
        url = urljoin(self.url, method)
        data = {
            "name": name
        }
        r = self.session.post(url, json=data)
        result = r.json()
        self.sections[name] = result['id']
        return result

    @staticmethod
    def escape_title(title):
        return title.replace('/', '-')

    def add_note(self, title, note, section_guid):
        print("Adding note '{}' to section {}".format(title, section_guid))
        method = 'v1.0/me/notes/sections/{}/pages'.format(section_guid)
        url = urljoin(self.url, method)
        data = self.note_template.format(title, note)
        r = self.session.post(url, data, headers={'content-type': 'application/xhtml+xml'})
        result = r.json()
        return result

    def move_notes(self, notebook_guid, section=None):
        notes = self.soup.find_all('note')
        for i, note in enumerate(notes, start=1):
            title = note.title.text
            if not section:
                section = self.title
            if not self.section_exists(section):
                self.create_section(notebook_guid, section)
            section_id = self.sections[section]
            note_text = note.content.text
            notebook_name = self.notebooks_by_id[notebook_guid]
            print("Adding note {} to Section {} in Notebook {}".format(i, section, notebook_name))
            self.add_note(title, note_text, section_id)
        return

    def _make_soup(self, xml):
        with open(self.filename) as infile:
            enex = infile.read()
        enex = enex.replace('en-note', 'ennote')
        soup = BeautifulSoup(enex, 'xml')
        return soup

def test():
    tooner = Tooner(sys.argv[1])
    notebook = tooner.create_notebook('Evernote')
    for name in ('Alpha', 'Beta', 'Omega'):
        section = tooner.create_section(notebook['id'], name)
        tooner.add_note("<h1>Some test data man</h1>", section['id'])

def main():
    tooner = Tooner(sys.argv[1])
    notebook = tooner.create_notebook('justinzfactz')
    tooner.move_notes(notebook['id'])

if __name__ == '__main__':
    main()
