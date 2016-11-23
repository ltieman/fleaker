"""
fleaker_config
-------

fleaker_config is a simple example app intended to show how robust and powerful
Fleaker's configuration can be.

It is also used to augment the test suite.
"""

from setuptools import setup


setup(name='fleaker_config',
      version='0.0.1',
      description='Configuration examples for fleaker',
      url='https://github.com/croscon/fleaker',
      author='Croscon Consulting',
      author_email='hayden.chudy@croscon.com',
      license='BSD',
      packages=['fleaker_config'],
      zip_safe=False,
      long_description=__doc__,
      include_package_data=True,
      platforms='any',
      install_requires=[
          'Fleaker',
      ],
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Web Environment',
          'Framework :: Flask',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Software Development :: Libraries :: Application Frameworks',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ])
