.. _api:

API
===

.. module:: fleaker

This section of the documentation covers Fleaker's external API and all of it's
possible interfaces. It is a combination of Fleaker's own documentation, with
links to relevant external packages where appropriate.

Standard Application
--------------------

.. autoclass:: App
   :members:


.. _default-mixins:

Default Mixins
--------------

The standard Fleaker style for implementing new functionality is to provide
a light-weight class that extends :class:`BaseApplication`, add all
functionality there through various hooks and helper methods, and then to add
that to the inheritance chain of :class:`App`. This allows the end developer to
reimplement their own custom Application object that doesn't necessarily have
everything :class:`App` does, but only has what they need. This also allows
easy integration of certain Fleaker features, into existing Applications and
projects, with little work. Please see :ref:`building-your-own-app` for more
information.

The standard Fleaker :class:`App` comes with the following mixins:

.. module:: fleaker.config

.. autoclass:: MultiStageConfigurableApp
   :members:
