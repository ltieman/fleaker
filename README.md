# Fleaker

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
