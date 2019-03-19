from setuptools import setup, find_packages

setup(
    name='openchemistry-molecules',
    version='0.1.0',
    description='Molecular data, containers and RESTful API.',
    packages=find_packages(),
    install_requires=[
      'girder>=3.0.0a5',
      'jsonpath-rw==1.4.0',
      'avogadro==1.92.1',
      'openbabel==1.8.2',
      'chemspipy==1.0.4',
      'pyparsing==2.0.5',
      'rdflib==4.2.1',
      'openchemistry'
    ],
    entry_points={
      'girder.plugin': [
          'molecules = molecules:MoleculesPlugin'
      ]
    }
)
