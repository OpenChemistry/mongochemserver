from setuptools import setup

setup(
    name='openchemistry-queues',
    version='0.1.0',
    description='Queue system for taskflows',
    packages=['openchemistryqueues'],
    install_requires=[
      'girder>=3.0.0a5',
      # Add these in when they have been modified for use with girder 3.x
      #'cumulus',
      #'taskflows'
    ],
    entry_points={
      'girder.plugin': [
          'openchemistryqueues = openchemistryqueues:QueuePlugin'
      ]
    }
)
