# ~*~ coding: utf-8 ~*~
"""Module that contains a Marshmallow schema that generate JSON schemas.

JSON Schemas can be a pain to write by hand. For example, the product
requirements change, thus your schema changes. If you are maintaining your
schemas by hand, you have to go through all of them and update them, or, even
worse, you just don't maintain them. With this class, you should never need to
hand write a JSON Schema again. Just pass your schema to it and it'll generate
it for you.

Example:
    This module is super easy to use. All you need to do is pass a schema or
    a Python path to a schema and this library will do the rest for you!

    .. code-block:: python

        # This is the schema we want to generate the schema for.
        class UserSchema(Schema):
            first_name = fields.String(**STR_REQUIRED)
            last_name = fields.String(**STR_REQUIRED)
            phone = PhoneNumberField(**REQUIRED)
            company_id = ForeignKeyField(**REQUIRED)
            joined = PendulumField(format='iso', **REQUIRED)
            last_login = ArrowField(allow_none=True, format='iso')

            class Meta(object):
                # This will dictate the filename that this schema will be
                # dumped to. If not provided, the filename will be
                # UserSchema.json
                json_schema_filename = 'user.json'

        # You can dump the schema to a file in a folder
        json_schema = FleakerJSONSchema.write_schema_to_file(
            # This library doesn't care if the schema has been initialized
            UserSchema,
            # The folder to write this schema to
            folder='docs/raml/schemas',
            # The context can control certain things about how the schema will
            # be dumped.
            context={'dump_schema': True}
        )

        # Now, you can find the dumped schema in docs/raml/schemas/user.json
        # You also have the end result stored in the json_schema variable

        # If you'd like for fine grained control over the filename or want to
        # use the file object further, a file pointer can be passed to the
        # creation method.
        with open('user_schema.json', 'w') as fp:
            FleakerJSONSchema.write_schema_to_file(UserSchema, file_pointer=fp)

        # Maybe you just want the schema in dict form. Super easy.
        json_schema = FleakerJSONSchema.generate_json_schema(
            # For all creation methods in this module can be loaded either by
            # the instance/class of the schema or by passing a Python path to
            # it, like so.
            'app.schemata.user.UserSchema'
        )

"""

import decimal
import json
import os.path

from inspect import isclass
from importlib import import_module
from sys import stdout

from marshmallow import Schema
from marshmallow_jsonschema import JSONSchema
from marshmallow_jsonschema.base import TYPE_MAP

from fleaker._compat import string_types
from fleaker.constants import DEFAULT_DICT, MISSING


# Update the built in TYPE_MAP to match our style better
TYPE_MAP.update({
    int: {
        'type': 'integer',
    },
    float: {
        'type': 'number',
    },
    decimal.Decimal: {
        'type': 'number',
    },
})


class FleakerJSONSchema(JSONSchema):
    """Marshmallow schema that can be used to generate JSON schemas."""

    @classmethod
    def generate_json_schema(cls, schema, context=DEFAULT_DICT):
        """Generate a JSON Schema from a Marshmallow schema.

        Args:
            schema (marshmallow.Schema|str): The Marshmallow schema, or the
                Python path to one, to create the JSON schema for.

        Keyword Args:
            file_pointer (file, optional): The path or pointer to the file
                to write this schema to. If not provided, the schema will be
                dumped to ``sys.stdout``.

        Returns:
            dict: The JSON schema in dictionary form.
        """
        schema = cls._get_schema(schema)

        # Generate the JSON Schema
        return cls(context=context).dump(schema).data

    @classmethod
    def write_schema_to_file(cls, schema, file_pointer=stdout,
                             folder=MISSING, context=DEFAULT_DICT):
        """Given a Marshmallow schema, create a JSON Schema for it.

        Args:
            schema (marshmallow.Schema|str): The Marshmallow schema, or the
                Python path to one, to create the JSON schema for.

        Keyword Args:
            file_pointer (file, optional): The pointer to the file to write
                this schema to. If not provided, the schema will be dumped to
                ``sys.stdout``.
            folder (str, optional): The folder in which to save the JSON
                schema. The name of the schema file can be optionally
                controlled my the schema's ``Meta.json_schema_filename``. If
                that attribute is not set, the class's name will be used for
                the filename. If writing the schema to a specific file is
                desired, please pass in a ``file_pointer``.
            context (dict, optional): The Marshmallow context to be pushed to
                the schema generates the JSONSchema.

        Returns:
            dict: The JSON schema in dictionary form.
        """
        schema = cls._get_schema(schema)
        json_schema = cls.generate_json_schema(schema, context=context)

        if folder:
            schema_filename = getattr(
                schema.Meta,
                'json_schema_filename',
                '.'.join([schema.__class__.__name__, 'json'])
            )
            json_path = os.path.join(folder, schema_filename)
            file_pointer = open(json_path, 'w')

        json.dump(json_schema, file_pointer, indent=2)

        return json_schema

    @classmethod
    def _get_schema(cls, schema):
        """Method that will fetch a Marshmallow schema flexibly.

        Args:
            schema (marshmallow.Schema|str): Either the schema class, an
                instance of a schema, or a Python path to a schema.

        Returns:
            marshmallow.Schema: The desired schema.

        Raises:
            TypeError: This is raised if the provided object isn't
                a Marshmallow schema.
        """
        if isinstance(schema, string_types):
            schema = cls._get_object_from_python_path(schema)

        if isclass(schema):
            schema = schema()

        if not isinstance(schema, Schema):
            raise TypeError("The schema must be a path to a Marshmallow "
                            "schema or a Marshmallow schema.")

        return schema

    @staticmethod
    def _get_object_from_python_path(python_path):
        """Method that will fetch a Marshmallow schema from a path to it.

        Args:
            python_path (str): The string path to the Marshmallow schema.

        Returns:
            marshmallow.Schema: The schema matching the provided path.

        Raises:
            TypeError: This is raised if the specified object isn't
                a Marshmallow schema.
        """
        # Dissect the path
        python_path = python_path.split('.')
        module_path = python_path[:-1]
        object_class = python_path[-1]

        if isinstance(module_path, list):
            module_path = '.'.join(module_path)

        # Grab the object
        module = import_module(module_path)
        schema = getattr(module, object_class)

        if isclass(schema):
            schema = schema()

        return schema
