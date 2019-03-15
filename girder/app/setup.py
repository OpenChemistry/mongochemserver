from setuptools import setup, find_packages

setup(
    name='openchemistry-app',
    version='0.0.1',
    description='Saves configuration data for OpenChemistry app.',
    packages=find_packages(),
    install_requires=[
      'girder>=3.0.0a5'
    ],
    entry_points={
      'girder.plugin': [
          'openchemistryapp = openchemistryapp:OpenChemistryAppPlugin'
      ]
    }
)
