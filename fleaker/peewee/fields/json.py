# ~*~ coding: utf-8 ~*~
"""
fleaker.peewee.fields.json
~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom Peewee field that allows for transparent storage of JSON data in
a Peewee database. This field uses the :func:`flask.json` proxy, which falls
back to :mod:`json` module out side of Flask application contexts, so any field
defined in :class:`fleaker.json.JSONEncoder` will work when serializing data.

Example:
    This field can be used like any other Peewee field. Simply assign a field
    this type.

    .. code-block:: python

        from collections import OrderedDict

        import peewee

        from werkzeug.datastructures import ImmutableDict

        from fleaker import db
        from fleaker.peewee import JSONField

        class Model(db.Model):
            reg_json_field = JSONField()
            # The JSON field can be ordered upon loading...
            ordered_json_field = JSONField(ordered=True)
            # ...this can also be set explictly.
            explict_ordered_json_field = JSONField(
                object_pairs_hook=OrderedDict
            )
            # The JSON field can be made immutable upon loading...
            immutable_json_field = JSONField(immutable=True)
            # ...this too can be set explictly.
            explict_immutable_json_field = JSONField(
                object_pairs_hook=ImmutableDict
            )

"""

from collections import OrderedDict

import flask.json

from peewee import TextField
from werkzeug.datastructures import ImmutableDict


class JSONField(TextField):
    """Peewee field that will load and dump JSON to and from the database.

    @TODO Get this working for searching using JSON searching.

    Keyword Args:
        This field takes all the same arguments as :class:`peewee.TextField`,
        as well as:

        object_hook (dict, optional):
            This will be passed to :func:`json.loads` keyword arguments with
            the same name and will effect what dictionary like object the value
            will be returned as.
        object_pairs_hook (dict, optional):
            This will be passed to :func:`json.loads` keyword arguments and
            will cause the retured dict to be first passed to it's constructor
            as a tuple key-value pair. If ``object_hook`` is provided, this
            value is ignored.
        ordered (bool, optional):
            Will return the dict as a :class:`collections.OrderedDict` when
            loaded from the database.
        immutable (bool, optional):
            Will return the dict as
            a :class:`werkzeug.datastructures.ImmutableDict` when the value is
            loaded from the database. This arg will override the
            ``object_pairs_hook`` when set to ``True``.
        immutable (bool, optional):
            Will return the dict as
            a :class:`werkzeug.datastructures.ImmutableDict` when the value is
            loaded from the database. This arg will override the
            ``object_pairs_hook`` when set to ``True``.
    """

    _load_kwarg_keys = ('object_hook', 'object_pairs_hook')

    def __init__(self, **kwargs):
        self._load_kwargs = {}

        for key in self._load_kwarg_keys:
            if kwargs.get(key):
                self._load_kwargs[key] = kwargs.pop(key)

        if kwargs.pop('immutable', False):
            self._load_kwargs['object_pairs_hook'] = ImmutableDict

        if kwargs.pop('ordered', False):
            self._load_kwargs['object_pairs_hook'] = OrderedDict

        super(JSONField, self).__init__(**kwargs)

    def python_value(self, value):
        """Return the JSON in the database as a ``dict``.

        Returns:
            dict: The field run through json.loads
        """
        value = super(JSONField, self).python_value(value)

        if value is not None:
            return flask.json.loads(value, **self._load_kwargs)

    def db_value(self, value):
        """Store the value in the database.

        If the value is a dict like object, it is converted to a string before
        storing.
        """
        # Everything is encoded being before being surfaced
        value = flask.json.dumps(value)

        return super(JSONField, self).db_value(value)
