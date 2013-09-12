from setuptools import setup, find_packages
import sys, os

version = '2.2.8'

setup(name='p2v',
      version=version,
      description="Physical To Virtual",
      long_description="""\
Transforme un serveur physique en serveur virtual xen""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='p2v xen',
      author='KOVAC Arnaud',
      author_email='arnaud.kovac@gmail.com',
      url='https://github.com/kirbs/P2V',
      license='GNU',
      packages=['p2v'],
      #packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [console_scripts]
      convert-p2v-xen=p2v.convert_p2v:main
      """,
      )
