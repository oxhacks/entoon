import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = 'https://www.onenote.com/api/'
TOKEN = ""
RESERVED_CHARS = '?*\\/:<>|&#''%~'

class Tooner:
    def __init__(self, filename, url=BASE_URL, token=TOKEN):
        self.url = url
        self.filename = filename
        self.token = token
        self.sections = {}
        self.notebooks = {}
        self._create_session()
        self._make_soup(filename)
        self.note_template = """
            <?xml version="1.0" encoding="utf-8" ?>
            <html xmlns="http://www.w3.org/1999/xhtml" lang="en-us">
                <head><title>{}</title></head>
                <body>{}</body>
            </html>
        """

    def notebook_exists(self, notebook):
        return notebook in self.notebooks

    def section_exists(self, section):
        return section in self.sections

    def _create_session(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': TOKEN
        })

    def create_notebook(self, name):
        method = 'v1.0/me/notes/notebooks'
        url = urljoin(BASE_URL, method)
        data = {
            "name": name
        }
        r = self.session.post(url, json=data)
        result = r.json()
        self.notebooks['name'] = result['id']
        return result

    def create_section(self, notebook_guid, name):
        method = 'v1.0/me/notes/notebooks/{}/sections'.format(notebook_guid)
        url = urljoin(BASE_URL, method)
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

    def add_note(self, title, note, guid):
        method = 'v1.0/me/notes/sections/{}/pages'.format(guid)
        url = urljoin(BASE_URL, method)
        data = self.note_template.format(title, note)
        r = self.session.post(url, data, headers={'content-type': 'application/xhtml+xml'})
        result = r.json()
        return result

    def move_notes(self, notebook_guid):
        notes = self.soup.find_all('note')
        for i, note in enumerate(notes):
            title = note.title.text
            section = 'Evernote'
            section = self.escape_title(section)
            if not self.section_exists(section):
                self.create_section(notebook_guid, section)
            section_id = self.sections[section]
            print(note)
            note_text = note.find_all('en-note')
            print(note_text)
            print("Adding note {} to Notebook {}".format(i, section))
            self.add_note(title, note_text, section_id)
        return

    def _make_soup(self, xml):
        with open(self.filename) as infile:
            enex = infile.read()
        self.soup = BeautifulSoup(enex, 'xml')
        return

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
