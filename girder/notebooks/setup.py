from setuptools import setup, find_packages

setup(
    name='openchemistry-notebooks',
    version='0.1.0',
    description='Populates new user accounts with sample notebooks.',
    packages=find_packages(),
    install_requires=[
      'girder>=3.0.0a5',
      'nbconvert==6.3.0'
    ],
    entry_points={
      'girder.plugin': [
          'notebooks = notebooks:NotebooksPlugin'
      ]
    }
)
