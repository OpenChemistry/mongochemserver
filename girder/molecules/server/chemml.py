import json
from openchemistry.io.base import BaseReader

# Trivial Chemml reader
class ChemmlReader(BaseReader):
    def read(self):
        return json.load(self._file)
