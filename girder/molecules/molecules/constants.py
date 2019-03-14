class PluginSettings:
    VIRTUOSO_BASE_URL = 'molecules.virtuoso.base_url'
    VIRTUOSO_RDF_UPLOAD_PATH = 'molecules.virtuoso.rdf_upload_path'
    VIRTUOSO_USER = 'molecules.virtuoso.user'
    VIRTUOSO_PASSWORD = 'molecules.virtuoso.password'
    SEMANTIC_URI_BASE = 'molecules.semantic.url_base'

theory_priority = {
    'mm': 10, # (molecular mechanics)
    'mp7': 20, # (semi-empirical)
    'rhf': 30, # (hartree fock, etc)
    'scf': 30, # (hartree fock, etc)
    'dft': 40,
    'mp2': 100,
    'ccsd': 200 # (coupled cluster)
}
