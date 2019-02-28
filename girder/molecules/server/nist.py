import re
import requests
import os
from bs4 import BeautifulSoup


# Variables controlled by admins
JDX_PATH = 'nist/jdx/'
NIST_URL = 'http://webbook.nist.gov/cgi/cbook.cgi'


def search_nist_inchi(inchi, stype='IR'):
    """Search NIST using the specified InChI or InChIKey

    This function queries and returns the matching NIST ID.

    Parameters
    ----------
    inchi : str
        An Inchi string.
    stype : str
        Type of spectrum to be downloaded.
    """
    EXACT_RE = re.compile('/cgi/cbook.cgi\?GetInChI=(.*?)$')

    print('Searching: {}' .format(inchi))
    response = requests.get(NIST_URL, params={'InChI': inchi, 'Units': 'SI'})
    soup = BeautifulSoup(response.text)
    idlink = soup.find('a', href=EXACT_RE)
    if idlink:
        nistid = re.match(EXACT_RE, idlink['href']).group(1)
        print('Result: {}' .format(nistid))
        return nistid


def get_jdx(nistid, stype='IR'):
    """Download jdx file for the specified NIST ID."""
    filepath = os.path.join(JDX_PATH, '{}-{}.jdx' .format(nistid, stype))
    if os.path.isfile(filepath):
        print('{} {}: Already exists at {}' .format(nistid, stype, filepath))
        return
    print('{} {}: Downloading' .format(nistid, stype))
    response = requests.get(NIST_URL, params={'JCAMP': nistid, 'Type': stype,
                                              'Index': 0})
    if response.text == '##TITLE=Spectrum not found.\n##END=\n':
        print('{} {}: Spectrum not found' .format(nistid, stype))
        return
    print('Saving {}' .format(filepath))
    with open(filepath, 'wb') as file:
        file.write(response.content)
