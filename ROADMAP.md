Thoughts and ideas:

* Install Fleaker as a console entrypoint
  * First task: `fleaker scaffold`
    * Scaffold a basic Flaker project.
    * Pass a `--template=$URL` where $URL is a git repository and it hooks into
      cookiecutter for you and just GOES!
* Wrap up the ORMS.
  * Pick either SQLA or PeeWee, at install time.
  * Provides and sets up your singleton for you.
  * Fails to import if neither model is backend is installed.
    * Use pytest marks to test specific backends or no backend.
  * Probably some sort of DBAwareComponent.
* Wrap up Marshmallow.
  * Wrap up Webargs?
* Setup the function that registers the login manager.
  * Takes an argument of a component that it can pull functions with matching
    names from. No more top level functions!
  * Make it part of `App.create_app`
* Setup the function that registers logging.
  * Configured via config values? Only if params are missing, like it is now.
  * Make it part of `App.create_app`.
* Create `App.create_app`, which is the magic app factory for you.
* Blueprint registration.
  * `App.register_blueprints(import_path)` searches import path and attempts to
    automatically register blueprints for you searching for named files or
    classes, or something. Also just takes one or more blueprints.
* Various util functions as needed.
* Probably something to set Sentry up.
