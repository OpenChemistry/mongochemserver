from setuptools import setup, find_packages

setup(
    name='openchemistry-images',
    version='0.0.1',
    description='Keep track of images used in OpenChemistry.',
    packages=find_packages(),
    install_requires=[
      'girder>=3.0.0a5',
      'girder_client'
    ],
    entry_points={
      'girder.plugin': [
          'images = images:ImagesPlugin'
      ]
    }
)
