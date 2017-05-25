# ~*~ coding: utf-8 ~*~
"""
Fleaker
-------

Fleaker is a framework built on top of Flask that aims to make using Flask
easier and more productive, while promoting best practices.

Yes, it's BSD licensed.

Easier to Setup
```````````````

Save in an app.py:

.. code:: python

    import os

    from fleaker import App

    def create_app():
        app = App.create_app(__name__)
        settings_dict = {'DEBUG': True}
        app.configure('.settings', os.env, settings_dict)

        return app

    if __name__ == '__main__':
        create_app().run()

Just as Easy to Use
```````````````````

Run it:

.. code:: bash

    $ pip install fleaker
    $ python app.py
     * Running on http://localhost:5000/
"""

import ast
import re

from setuptools import setup


def install():
    """Install Fleaker.

    In a function so we can protect this file so it's only run when we
    explicitly invoke it and not, say, when py.test collects all Python
    modules.
    """
    _version_re = re.compile(r"__version__\s+=\s+(.*)")  # pylint: disable=invalid-name

    with open('./fleaker/__init__.py', 'rb') as file_:
        version = ast.literal_eval(_version_re.search(  # pylint: disable=invalid-name
            file_.read().decode('utf-8')).group(1))

    download_url = ('https://github.com/croscon/fleaker/archive/'
                    'v{}.tar.gz'.format(version))

    setup(
        name='fleaker',
        version=version,
        download_url=download_url,
        description='Tools and extensions to make Flask development easier.',
        url='https://github.com/croscon/fleaker',
        author='Croscon Consulting',
        author_email='open.source@croscon.com',
        license='BSD',
        packages=[
            'fleaker',
            'fleaker.marshmallow',
            'fleaker.marshmallow.fields',
            'fleaker.peewee',
            'fleaker.peewee.fields',
            'fleaker.peewee.mixins',
            'fleaker.peewee.mixins.time',
        ],
        zip_safe=False,
        long_description=__doc__,
        include_package_data=True,
        platforms='any',
        install_requires=[
            'Flask',
            'Flask-Classful',
            'Flask-Login',
            'Flask-Marshmallow',
            'arrow',
            'bcrypt',
            'blinker',
            'marshmallow',
            'marshmallow-jsonschema',
            'peewee',
            'pendulum',
            'phonenumbers',
        ],
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Environment :: Web Environment',
            'Framework :: Flask',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            # @TODO: Pick specific Python versions; out of the gate flask does 2.6,
            # 2.7, 3.3, 3.4, and 3.5
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
            'Topic :: Software Development :: Libraries :: Application Frameworks',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        keywords=['flask', 'web development', 'flask extension']
    )


if __name__ == '__main__':
    install()
