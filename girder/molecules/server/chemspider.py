import os
from chemspipy import ChemSpider

chemspikey = os.environ['chemspikey']

def find_common_name(inchikey, formula):
    # Try to find the common name for the compound, if not use the formula.
    cs = ChemSpider(chemspikey)

    name = formula

    if (len(inchikey) > 0):
      result = cs.search(inchikey)
      if (len(result) == 1):
        name = result[0].common_name

    return name
