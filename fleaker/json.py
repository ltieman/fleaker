# -*- coding: utf-8 -*-
"""
fleaker.json
~~~~~~~~~~~~

Custom JSON classes so more complex objects can be serialized by Flask. This
will be your default JSON Encoder if you use the standard Fleaker app.
"""

from __future__ import absolute_import

import datetime
import decimal
import json

from collections import OrderedDict

import arrow
import pendulum
import phonenumbers
import flask

from ._compat import text_type
from .base import BaseApplication


class FleakerJSONEncoder(flask.json.JSONEncoder):
    """Custom JSON encoder that will serialize more complex datatypes.

    This class adds support for the following datatypes:

    - ``phonenumbers.phonenumber.PhoneNumber``: This will be serialized to
        a E.164 phonenumber. This will only be run if ``phonenumbers`` is
        installed.
    - ``decimal.Decimal``: This will serialize to a pretty decimal number with
        no trailing zeros and no unnecessary values. For example:
        - 2.01 -> 2.01
        - 2.0 -> 2
        - 2.010 -> 2.01
        - 2.000 -> 2
    - ``arrow.Arrow``: This will be serialized to an ISO8601 datetime string
        with the offset included.
    - ``datetime.datetime``: This will be serialized to an ISO8601 datetime
        string with the offset included.
    - ``datetime.date``: This will be serialized to an ISO8601 date string.

    It should be noted that Flask has started supporting ``datetime.datetime``
    and ``datetime.date``, but they serialize it to the locality's default and
    not ISO8601. This isn't really acceptable for our use cases, so we will
    continue to override those types.

    Extended from http://flask.pocoo.org/snippets/119/.

    .. versionadded:: 0.1.0
       This has been the default JSONEncoder since Fleaker's inception.
    """

    # @TODO (json, doc): Fix links in above; intersphinx to libs.

    def default(self, obj):
        """Encode individual objects into their JSON representation.

        This method is used by :class:`flask.json.JSONEncoder` to encode
        individual items in the JSON object.

        Args:
            obj (object): Any Python object we wish to convert to JSON.

        Returns:
            str: The stringified, valid JSON representation of our provided
                object.
        """
        if isinstance(obj, decimal.Decimal):
            obj = format(obj, 'f')
            str_digit = text_type(obj)

            return (str_digit.rstrip('0').rstrip('.')
                    if '.' in str_digit
                    else str_digit)

        elif isinstance(obj, phonenumbers.PhoneNumber):
            return phonenumbers.format_number(
                obj,
                phonenumbers.PhoneNumberFormat.E164
            )

        elif isinstance(obj, pendulum.Pendulum):
            return text_type(obj)

        elif isinstance(obj, arrow.Arrow):
            return text_type(obj)

        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()

        try:
            return list(iter(obj))
        except TypeError:
            pass

        return super(FleakerJSONEncoder, self).default(obj)

    def encode(self, obj):
        if isinstance(obj, OrderedDict):
            return json.dumps(obj)

        return super(FleakerJSONEncoder, self).encode(obj)


class FleakerJSONApp(BaseApplication):
    """App class mixin that defines a custom JSON encoder.

    Please see :ref:`json-encoding` for more details.

    Attributes:
        json (flask.json): An alias to ``flask.json`` so it can be accessed via
            the app because that's convenient.
        json_encoder (json.JSONEncoder): The JSON encoder that the App should
            use by default.

    .. versionadded:: 0.1.0
       This has been around since before Fleaker was made public.
    """

    def __init__(self, import_name, **kwargs):
        super(FleakerJSONApp, self).__init__(import_name, **kwargs)

        # @TODO (json): Should be class level to make this easier to override.
        self.json_encoder = FleakerJSONEncoder
        self.json = flask.json
        self.config.setdefault('JSON_SORT_KEYS', True)
