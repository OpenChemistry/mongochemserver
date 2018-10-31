import cclib
import json
import tempfile

def _cclib_to_cjson_basis(basis):
    shell_type_map = {
        's': 0,
        'p': 1,
        'd': 2,
        'f': 3,
        'g': 4,
        'h': 5,
        'i': 6,
        'k': 7,
        'l': 8,
        'm': 9,
        'n': 10,
        'o': 11
    }
    coefficients = []
    exponents = []
    primitives_per_shell = []
    shell_to_atom_map = []
    shell_types = []
    for i_atom, atom_basis in enumerate(basis):
        for shell in atom_basis:
            l_label, primitives = shell
            n_primitives = len(primitives)
            shell_to_atom_map.append(i_atom)
            primitives_per_shell.append(n_primitives)
            shell_types.append(shell_type_map[l_label.lower()])
            for primitive in primitives:
                exponents.append(primitive[0])
                coefficients.append(primitive[1])
    cjson_basis = {
        'coefficients': coefficients,
        'exponents': exponents,
        'primitivesPerShell': primitives_per_shell,
        'shellToAtomMap': shell_to_atom_map,
        'shellTypes': shell_types
    }
    return cjson_basis

def _cclib_to_cjson_mocoeffs(coeffs):
    cjson_coeffs = []
    # only take the orbitals at the end of the optimization
    for mo in coeffs[-1]:
        cjson_coeffs.extend(mo)
    return cjson_coeffs

def _cclib_to_cjson_vibdisps(vibdisps):
    cjson_vibdisps = []
    for vibdisp in vibdisps:
        cjson_vibdisps.append(list(vibdisp.flatten()))
    return cjson_vibdisps

def convert_str(str_data):
    with tempfile.TemporaryFile('w+') as tf:
        tf.write(str_data)
        tf.seek(0)
        data = cclib.io.ccread(tf)
    
    cjson = json.loads(cclib.ccwrite(data, outputtype='cjson',))

    # The cjson produced by cclib is not directly usable in our platform
    # Basis, moCoefficients, and normal modes need to be further converted

    # Cleanup original cjson
    if 'orbitals' in cjson['atoms']:
        del cjson['atoms']['orbitals']
    if 'properties' in cjson:
        del cjson['properties']
    if 'vibrations' in cjson:
        del cjson['vibrations']
    if 'optimization' in cjson:
        del cjson['optimization']
    if 'diagram' in cjson:
        del cjson['diagram']
    if 'inchi' in cjson:
        del cjson['inchi']
    if 'inchikey' in cjson:
        del cjson['inchikey']
    if 'smiles' in cjson:
        del cjson['smiles']

    # Convert basis set info
    if hasattr(data, 'gbasis'):
        basis = _cclib_to_cjson_basis(data.gbasis)
        cjson['basisSet'] = basis

    # Convert mo coefficients
    if hasattr(data, 'mocoeffs'):
        mocoeffs = _cclib_to_cjson_mocoeffs(data.mocoeffs)
        cjson.setdefault('orbitals', {})['moCoefficients'] = mocoeffs
    
    # Convert mo energies
    if hasattr(data, 'moenergies'):
        moenergies = list(data.moenergies[-1])
        cjson.setdefault('orbitals', {})['energies'] = moenergies

    if hasattr(data, 'nelectrons'):
        cjson.setdefault('orbitals', {})['electronCount'] = int(data.nelectrons)
    
    if hasattr(data, 'homos') and hasattr(data, 'nmo'):
        homos = data.homos
        nmo = data.nmo
        if len(homos) == 1:
            occupations = [2 if i <= homos[0] else 0 for i in range(nmo)]
            cjson.setdefault('orbitals', {})['occupations'] = occupations

    # Convert normal modes
    if hasattr(data, 'vibfreqs'):
        vibfreqs = list(data.vibfreqs)
        cjson.setdefault('vibrations', {})['frequencies'] = vibfreqs

    if hasattr(data, 'vibdisps'):
        vibdisps = _cclib_to_cjson_vibdisps(data.vibdisps)
        cjson.setdefault('vibrations', {})['eigenVectors'] = vibdisps
    
    # Convert calculation metadata
    if hasattr(data, 'metadata'):
        metadata = data.metadata
        if 'basis_set' in metadata:
            cjson.setdefault('metadata', {})['basisSet'] = metadata['basis_set'].lower()
        if 'functional' in metadata:
            cjson.setdefault('metadata', {})['functional'] = metadata['functional'].lower()
        if 'methods' in metadata:
            cjson.setdefault('metadata', {})['theory'] = metadata['methods'][0].lower()

    return cjson