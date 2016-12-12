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

.. currentmodule:: fleaker.config

.. autoclass:: MultiStageConfigurableApp
   :members:

.. currentmodule:: fleaker.exceptions

.. autoclass:: ErrorAwareApp

.. currentmodule:: fleaker.json

.. autoclass:: FleakerJSONApp
   :members:

Exceptions
----------

Fleaker provides both a custom exception for itself, and a base custom
exception for your reuse. These are both backed by one class.

.. currentmodule:: fleaker.exceptions

.. autoclass:: FleakerBaseException
   :members:

.. autoclass:: FleakerException
   :members:

.. autoclass:: AppException
   :members:

Components
----------

Fleaker provides a new set of classes called :class:`~fleaker.Component`'s.
Component's should be used to hold all of your business logic and should
interact with your models from your views. See the :doc:`components` page for
more info.

.. currentmodule:: fleaker.component

.. autoclass:: Component
   :members:

ORM Integration
---------------

Fleaker provides conveniences for automatically integrating and setting up the
PeeWee and SQLAlchemy ORM's. Please see :mod:`~fleaker.orm` for more
information.

.. currentmodule:: fleaker.orm

.. autoclass:: ORMAwareApp
   :members:

Marshmallow Support
-------------------

Fleaker provides a number of helpers for working with Marshmallow. Please see
:ref:`marshmallow` for more information.

.. currentmodule:: fleaker.marshmallow

Marshmallow Constants
---------------------

.. automodule:: fleaker.marshmallow.constants
   :members:

Marshmallow App Extensions
--------------------------

.. autoclass:: fleaker.marshmallow.extension.MarshmallowAwareApp
   :members:

Marshmallow Schema
------------------

.. autoclass:: fleaker.marshmallow.schema.Schema
   :members:

Marshmallow Fields
------------------

.. autoclass:: fleaker.marshmallow.fields.arrow.ArrowField
   :members:

.. autoclass:: fleaker.marshmallow.fields.foreign_key.ForeignKeyField
   :members:

.. autoclass:: fleaker.marshmallow.fields.mixin.FleakerFieldMixin
   :members:

.. autoclass:: fleaker.marshmallow.fields.pendulum.PendulumField
   :members:

.. autoclass:: fleaker.marshmallow.fields.phone_number.PhoneNumberField
   :members:

Marshmallow JSON Schema Support
-------------------------------

.. automodule:: fleaker.marshmallow.json_schema
   :members:

.. _json-encoding:

JSON Encoding
-------------

Fleaker provides the :class:`~fleaker.json.FleakerJSONApp` to override JSON
encoding.  Internally, that app has to use a JSON Encoder, described below.
Override the :class:`~fleaker.json.FleakerJSONEncoder` and set it as the
``json_encoder`` for your own custom App to provide further customization.

.. currentmodule:: fleaker.json

.. autoclass:: FleakerJSONEncoder
   :members:

Constants
---------

Fleaker provides a few common constants that can be imported and reused across
projects. Please see :mod:`~fleaker.missing` for more information.

.. automodule:: fleaker.constants

Sentinels
---------

Fleaker provides a few custom classes that aid in creating standard Python
"Sentinel" objects. Please see :mod:`~fleaker.missing` for more information.

.. currentmodule:: fleaker.missing

.. autoclass:: MissingSentinel

.. autoclass:: MissingDictSentinel

Utils
-----

Utils are small helper functions that make working with Flask a little easier.

.. autofunction:: fleaker.utils.in_app_context

Extension Classes
-----------------

The Fleaker :class:`BaseApplication` is not something the standard developer
will need to know about. However, if you intend to contribute to or extend
Fleaker, then it is of the utmost importance.

.. currentmodule:: fleaker.base

.. autoclass:: BaseApplication
   :members:
