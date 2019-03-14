import re
import requests
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

    response = requests.get(NIST_URL, params={'InChI': inchi, 'Units': 'SI'})
    soup = BeautifulSoup(response.text)
    idlink = soup.find('a', href=EXACT_RE)
    if idlink:
        nistid = re.match(EXACT_RE, idlink['href']).group(1)
        return nistid


def get_jdx(nistid, stype='IR'):
    """Get jdx file content for the specified NIST ID."""
    response = requests.get(NIST_URL, params={'JCAMP': nistid, 'Type': stype,
                                              'Index': 0})
    if response.text == '##TITLE=Spectrum not found.\n##END=\n':
        return
    else:
        content = response.content.splitlines()
        content = [line.decode("utf-8") for line in content]
        return content
