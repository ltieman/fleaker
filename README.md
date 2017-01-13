# Fleaker

Fleaker makes Flask devlopment easier by including glue and customizations for
popular support libraries such as:

* Marshmallow
* PeeWee

In addition to implementing improved Flask apps with more powerful:

* Configuration
* Components
* Exceptions

All in all, Fleaker makes developing for Flask more like developing for Python:
it's batteries included and you'll always be surprised with what's already
built.

## Usage

The main way to begin using Fleaker is simply to import: `fleaker.App` and
then call `create_app`, like so:

```python
import os

from fleaker import App


def create_app():
    app = App.create_app(__name__)

    # configure from settings module, and then the OS environment
    app.configure('settings', os.environ)

    return app

if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=5000)
```

Run the above code and you can access your Flask app on: `localhost:500`!


## Development

To lint, run this:

```sh
tox -e lint
```

And it will run both `flake8` and `pylint` for you.

@TODO: Probably move to CONTRIBUTING.md.

## Fixing an issue

See a smelly lil' issue you wanna tackle? Awesome, here's how you do it, using a classic test-driven approach:

+ First you're going to want to clone the repository: `git clone git@github.com:croscon/fleaker.git` 
+ Write a test that produces the failure seen in the issue
	+ Run all tests with this command (py27 denotes a python 2 run environment): `tox -e py27`
	+ Run a specific test by passing in the location like so **(note the space)**: `tox -e py27 -- tests/path-to-test-file`
+ Write various similar tests to see how they respond
	+ If they fail, you can try to address them in the fix for the original issue
	+ If they pass, no problem.
+ Use tox to run the tests and utilize the stack trace to locate the source
+ Once the source is located, go forth and fix it
+ Run tests to ensure all is well
	+ Run tests with both the `-py27` and `-py33` flags to ensure success for both Python 2 and Python 3 


## The Dream

This is what setting up a Python app should look like:

```python
from os import env

from fleaker import App

from my_application.components import SessionComponent


def create_app():
    # below automatically imports settings local to __name__,
    app = App.create_app(__name__, login_component=SessionComponent)
    # should setup logging and proxy fix
    # do babel? marshmallow?
    # version management?
    # THIS should use Click for portability
    app.configure('.settings_common', '.settings_secret', env)
    app.register_blueprints('.blueprints')
    return app
```
