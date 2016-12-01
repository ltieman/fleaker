Thoughts and ideas:

* Finish the component stuff
  * There are a few skipped tests that need finishing.
  * Update tests to run with a base component and an overridden component to
    ensure naming is fine
  * Update the init_app methods to have a `persist` flag which when set to True,
    will make not restore the context back to it's original value whenever an
    appcontext is popped; let's you weave in and out of app contexts at will,
    like in the tests
    * some commented out code in test_multiple_apps to accomodate this
  * Update the `update_context` and `clear_context` methods to have an
    `update_original` method which will update the original stored context, so
    that whenever an app context is popped we restore back to that. Example: we
    init the app with a context of "foo"; no matter what we change it too when
    the app context is popped it goes back to "foo"; if we update the context
    and provide `update_original=True` such that the new context is "bar", then
    whenever we leave the app context, we go back to "bar"
    * There should be tests for this as well, those need writing
    * Likely requires us to update our CB map to be a three element tuple and
      store the original value, so we can update it; and then recreate the
      tuple anytime we update the original
    * EVERY call to `init_app` should pass `update_original=True` to
      `update_context`.
* Install Fleaker as a console entrypoint
  * First task: `fleaker scaffold`
    * Scaffold a basic Flaker project.
    * Pass a `--template=$URL` where $URL is a git repository and it hooks into
      cookiecutter for you and just GOES!
* Wrap up the ORMS.
  * Pick either SQLA or PeeWee, at install time. -- CHECK
  * Provides and sets up your singleton for you. -- CHECK
  * Fails to import if neither model is backend is installed.
    * Use pytest marks to test specific backends or no backend.
  * Probably some sort of DBAwareComponent.
  * Finish the ORM stuff; finish the SQLA stuff
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
