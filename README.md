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

# The Dream

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
