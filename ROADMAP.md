# Fleaker Roadmap

This document contains all future features that are currently planned for
Fleaker. Looser items are in the: [Thoughts and Ideas](#thoughts-and-ideas)
sections and anything ready for action is in the [Next Steps](#next-steps)
section.

## Next Steps

* Logging - 16 hours
  * Configured via a standardized series of config values. Takes arguments to
    create_app to override these values.
  * Extended via class variables, e.g., the standard logger is a class variable
    on our Fleaker app, that you can override, if needed.
  * Existing WIP here: https://github.com/croscon/fleaker/commit/fbcdcf4286a834c4224d3fca0865381c8411b5aa
* Flask-Login Integration - 24 hours
  * `App.create_app` now takes a class that we can pull the functions from;
    alternatively, you can just pass the functions in individually.
    * The motivation for this is so we can move away from top-level module
      functions and towards more static or class methods for login.
  * Login Manager directly exposed in the `fleaker` itself. For example, `from
    fleaker import login_manager` gives you the proxy.
  * Should add an extra method to explicitly re-init the login manager. For
    example, a `register_login_manager`, if registering it at app creation time
    simply isn't feasible.
* Sentry Integration - 8 hours
  * Adds an `extra_requires` for Sentry (e.g., `fleaker[sentry]`) that installs
    `raven`.
  * Adds a new composable app mixin for Sentry registration.
  * Sentry is still configured from the environment, as expected.
  * Adds a `post_configure` callback that will look for the proper config
    values and, when they are present, setup Sentry integration.
* Release Improvements - 8 hours
  * Some system to automate the creation of tags, writing of changelogs,
    version bumping and, eventually, upload to PyPI.
* Base Class for Flask-Classful - 16 hours
  * Encapsulate all of our existing Flask-Classful base views and expose them
    in some `BaseView` class.
  * Should **NOT** be an app mixin and should just be a regular class.
  * We can iterate on this later as we find new items.
* Automatic Blueprint Registration - 40 hours
  * This is still HIGHLY conceptual and experimental, so the final
    implementation may end up changing. My initial thoughts are:
    * `App.register_blueprints(import_path)` searches import path and attempts
      to automatically register blueprints for you searching for named files or
      classes.
    * Alternatively, this method also takes a series of classes that we should
      just register.
    * Could work with magic named methods, e.g., tries to import
      a `register_blueprints` from all module paths provided and, if found,
      runs that for you which is sort of your hook (similar to some of what
      pytest does for module level tests).
* Tasks Integration - 8 hours
  * For now, we will only expose our helper methods, such as `docker_task` to
    end users.
  * Should add a `fleaker.fabric` and `fleaker.invoke` package for housing our
    utility functions for import.
  * Eventually, as we work more with Click, we'll add a `fleaker.click` package
    that will contain all of that.
* Custom Test Class - 8 hours
  * This is fully described and documented in
    [#31](https://github.com/croscon/fleaker/issues/31).

## Thoughts and Ideas:

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
* Various util functions as needed.
* Tests for our compat stuff.
* Proper versioning and release stuff + contributing info + deploy docs + put
  on PyPI + a better README + better general pkg management in general
* Change how the standard app is made.
  * Should be made like so:
    ```python
    App = create_app_class(MultiStageConfigurableApp, ORMAwareApp)
    ```
    You basically define a `create_app_class` function that takes all the app
    mixins you want and properly strings them together. This is meant for
    people who know which mixins they want, allowing them to create that in one
    line. It's also easier to copy-paste around in answers.
  * Even though it can impact documentation for the standard app, I think we
    can work around that.
  * Other motivations for this are ensuring that the BaseApplication is the
    last base class in the MRO and any other order aware things we may need.
