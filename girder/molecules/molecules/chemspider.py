import os
from chemspipy import ChemSpider
from girder.constants import TerminalColor

try:
    chemspikey = os.environ['chemspikey']
except KeyError:
    chemspikey = None
    print(TerminalColor.warning('WARNING: chemspikey not set, common names will not be resolved.'))


def find_common_name(inchikey, formula):
    # Try to find the common name for the compound, if not use the formula.

    name = formula

    if chemspikey:
        cs = ChemSpider(chemspikey)

        if (len(inchikey) > 0):
          result = cs.search(inchikey)
          if (len(result) == 1):
            name = result[0].common_name

    return name
