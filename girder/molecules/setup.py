from setuptools import setup, find_packages

setup(
    name='openchemistry-molecules',
    version='0.1.0',
    description='Molecular data, containers and RESTful API.',
    packages=find_packages(),
    install_requires=[
      'girder>=3.0.0a5',
      'girder-jobs',
      'jsonpath-rw==1.4.0',
      'avogadro==1.92.1',
      'openbabel==2.4.1',
      'chemspipy==1.0.4',
      'pyparsing==2.0.5',
      'rdflib==4.2.1',
      'openchemistry',
      'beautifulsoup4',
      'jcamp',
      'requests',
      'requests-futures'
    ],
    entry_points={
      'girder.plugin': [
          'molecules = molecules:MoleculesPlugin'
      ]
    }
)
