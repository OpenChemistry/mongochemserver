from setuptools import setup

setup(
    name='openchemistry-notebooks',
    version='0.1.0',
    description='Populates new user accounts with sample notebooks.',
    packages=['openchemistrynotebooks'],
    install_requires=[
      'girder>=3.0.0a5',
      'nbconvert==5.4.1'
    ],
    entry_points={
      'girder.plugin': [
          'openchemistrynotebooks = openchemistrynotebooks:OpenChemistryNotebooksPlugin'
      ]
    }
)
