# ~*~ coding: utf-8 ~*~
"""
fleaker.peewee.mixins.event
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides a set of Peewee mixins that can be used for activity and
auditing tracking transparently with Peewee's event system. For example, using
the typical file system example, say you need to keep track of who created and
then modified a Folder. You could hack together inflexible code to meet this
criteria, sure. But then you need to keep track of who created and modified
a File. The second you introduce auditing into your system, you might as well
keep track of everything and this mixin allows for that quite easily!

There are two mixins in this module, the ``EventMixin`` and the
``EventStorageMixin``. The ``EventMixin`` should be placed into models in which
tracking the changes upon is desirable. The ``EventStorageMixin`` should be
provided to a model in order to track the activity in the system.

Because of how Peewee's event system works, event tracking only works when an
instance is created/updated using :func:`peewee.Model.save` or deleted using
:func:`peewee.Model.delete_instance`.

Since Fleaker does not provide migrations of any sort, you must create the
Event storage table yourself. Here is some SQL to create the bare essentials
for Event storage. Be sure to add foreign keys to the tables you'd like to
track the events for.

.. code-block:: sql

    CREATE TABLE `events` (
        `body` TEXT NULL,
        `code` VARCHAR(255) NOT NULL DEFAULT 'AUDIT',
        `version` VARCHAR(255) NULL,
        -- Feel free to use a JSON field or a text field, depending on your
        -- database of choice.
        `meta` JSON NULL,
        `original` JSON NULL,
        `updated` JSON NOT NULL,
        `model` VARCHAR(255) NULL,
        `created` DATETIME NOT NULL,
        `modified` DATETIME NULL
    )

Example:
    To use these mixins, add their classes to the model's inheritance chain. In
    this example, we will be using a file system with a User operating upon it.
    The goal of this example is to keep track of File and Folder movements,
    File and Folder creation, and File and Folder deletion. In all events
    created, we will keep track of the User causing these Events.

    .. code-block:: python

        import peewee

        from flask_login import login_user
        from fleaker.peewee import EventMixin, EventStorageMixin

        class User(EventMixin):
            # A user interacting with a file system.
            name = peewee.CharField(max_length=255)


        class Folder(EventMixin):
            # A folder in a file system.
            name = peewee.CharField(max_length=255)
            parent_folder = peewee.ForeignKeyField('self', null=True)

            class Meta:
                # In order to define custom events, for say a timeline, you
                # must use the DSL described here. The create_message variable
                # will create a custom event for when a Folder is created.
                create_message = {
                    # This the unique code to identify this event.
                    'code': 'FOLDER_CREATED',
                    # This is the human readable text describing this event. It
                    # should be noted that all text here is run through Jinja
                    # rendering. It should be noted that Jinja is rendered at
                    # runtime and not when the event is created.
                    #
                    # Also, the raw Event instance is passed to the Jinja
                    # rendering. This is useful so you can grab related info
                    # from the instance through relationships. In this example,
                    # the `created_by` is the creator of the event and you'll
                    # be able to pull the user's current name even if it
                    # changes in the future so you're feed make sense.
                    'message': ("{{event.created_by.name}} created "
                                "{{meta.folder.text}} in "
                                "{{meta.parent.text}}."),
                    # Meta is a special key that will pull values relative to
                    # the model being operated upon. This allows for caching of
                    # the state of the models that will not change event if the
                    # model it is representing changes.
                    'meta': {
                        # This value here will pull from the Folder's name in
                        # to the text field and the id into the id field.
                        'folder': {
                            'text': 'name',
                            'id': 'id',
                        },
                        # In this key, we are going to keep track of
                        # information of the current state of the parent
                        # folder.
                        'parent': {
                            # Note that we are giving it a relative path to the
                            # current instance.
                            'text': 'parent_folder.name',
                            'id': 'parent_folder.id',
                        },
                    },
                }
                # The delete_message syntax is the same as the create_message.
                delete_message = {
                    'code': 'FOLDER_DELETED',
                    'message': ("{{event.created_by.name}} deleted "
                                "{{meta.folder.text}} from "
                                "{{meta.parent.text}}."),
                    'meta': {
                        'folder': {
                            'text': 'name',
                            'id': 'id',
                        },
                        'parent': {
                            'text': 'parent_folder.name',
                            'id': 'parent_folder.id',
                        },
                    },
                }
                # The update message is the same as above with one key
                # difference. That is that it is a dictionary where the keys
                # represent fields that can change on the model and the values
                # are the DSLs above. This allows for multiple events to be
                # created if multiple fields change in one update operation.
                update_messages = {
                    # This event will be created if the Folder's name changes.
                    'name': {
                        'code': 'FOLDER_RENAMED',
                        'message': ("{{event.created_by.name}} renamed "
                                    "{{meta.og_folder.text}} to "
                                    "{{meta.folder.text}}."),
                        'meta': {
                            'og_folder': {
                                # original is a special key that will pull
                                # values from the record being operated upon
                                # before it is saved.
                                'text': 'original.name',
                                'id': 'original.id',
                            },
                            'folder': {
                                'text': 'name',
                                'id': 'id',
                            },
                        },
                    },
                    'parent_folder': {
                        'code': 'FOLDER_MOVED',
                        'message': ("{{event.created_by.name}} moved "
                                    "{{meta.folder.text}} from "
                                    "{{meta.og_parent.text}} to "
                                    "{{meta.parent.text}}."),
                        'meta': {
                            'folder': {
                                'text': 'name',
                                'id': 'id',
                            },
                            'og_parent': {
                                'text': 'original.parent_folder.name',
                                'id': 'original.parent_folder.id',
                            },
                            'parent': {
                                'text': 'parent_folder.name',
                                'id': 'parent_folder.id',
                            },
                        },
                    },
                }

            # All the events can be modified manually in a callback method.
            # This is useful if conditional logic is need to fill in
            # information for the events. For the create_event_callback and
            # delete_event_callback, a single event is passed. In the case of
            # the update_event_callback, a list of all events created for that
            # operation are passed in.
            #
            # In this case, if the parent folder of where the folder is being
            # moved from or to is null, the text that should be stored should
            # reflect that it's in the root of the file system.
            def create_event_callback(self, event):
                if not self.parent_folder:
                    event.meta['parent']['text'] = 'the root'

            def delete_event_callback(self, event):
                if not self.parent_folder:
                    event.meta['parent']['text'] = 'the root'

            def update_event_callback(self, events):
                for event in events:
                    if event.code == 'FOLDER_MOVED':
                        if not self.get_original().parent_folder:
                            event.meta['og_parent']['text'] = 'the root'

                        if not self.parent_folder:
                            event.meta['parent']['text'] = 'the root'


        class File(EventMixin):
            # A file in a file system.
            name = peewee.CharField(max_length=255)
            folder = peewee.ForeignKeyField(Folder, null=True)

            class Meta:
                create_message = {
                    'code': 'FILE_CREATED',
                    'message': ("{{event.created_by.name}} created "
                                "{{meta.file.text}} in "
                                "{{meta.folder.text}}."),
                    'meta': {
                        'file': {
                            'text': 'name',
                            'id': 'id',
                        },
                        'folder': {
                            'text': 'folder.name',
                            'id': 'folder_id',
                        },
                    },
                }
                delete_message = {
                    'code': 'FILE_DELETED',
                    'message': ("{{event.created_by.name}} deleted "
                                "{{meta.file.text}} from "
                                "{{meta.folder.text}}."),
                    'meta': {
                        'file': {
                            'text': 'name',
                            'id': 'id',
                        },
                        'folder': {
                            'text': 'folder.name',
                            'id': 'folder.id',
                        },
                    },
                }
                update_messages = {
                    'name': {
                        'code': 'FILE_RENAMED',
                        'message': ("{{event.created_by.name}} renamed "
                                    "{{meta.og_file.text}} to "
                                    "{{meta.file.text}}."),
                        'meta': {
                            'og_file' {
                                'text': 'original.name',
                                'id': 'original.id',
                            },
                            'file': {
                                'text': 'name',
                                'id': 'id',
                            },
                        },
                    },
                    'folder': {
                        'code': 'FILE_MOVED',
                        'message': ("{{event.created_by.name}} moved "
                                    "{{meta.file.text}} from "
                                    "{{meta.og_folder.text}} to "
                                    "{{meta.folder.text}}."),
                        'meta': {
                            'file': {
                                'text': 'name',
                                'id': 'id',
                            },
                            'og_folder': {
                                'text': 'original.folder.name',
                                'id': 'original.folder.id',
                            },
                            'folder': {
                                'text': 'folder.name',
                                'id': 'folder.id',
                            },
                        },
                    },
                }

            def create_event_callback(self, event):
                if not self.folder:
                    event.meta['folder']['text'] = 'the root'

            def delete_event_callback(self, event):
                if not self.folder:
                    event.meta['folder']['text'] = 'the root'

            def update_event_callback(self, events):
                for event in events:
                    if event.code == 'FILE_MOVED':
                        if not self.get_original().folder:
                            event.meta['og_folder']['text'] = 'the root'

                        if not self.folder:
                            event.meta['folder']['text'] = 'the root'


        class Event(EventStorageMixin):
            # Model that tracks Events.
            # The foreign keys defined here will attempt to pull the values
            # from other FKs on the target instance. All FKs added to this
            # model should be nullable because they won't always be there.
            folder = peewee.ForeignKeyField(Folder, null=True)
            file = peewee.ForeignKeyField(File, null=True)
            # The created_by field is a special field on the Event model. It
            # will always be set to the ID of flask_login's current_user, if
            # they are logged in. If this is null, it should be assumed that
            # this was created by a system user.
            created_by = peewee.ForeignKeyField(User, null=True)

        # Create a User and log them in. This will be the User that causes all
        # the events.
        logged_in_user = User(name="Tom Hanks")
        logged_in_user.save()
        login_user(logged_in_user)

        # Now let's create a Folder
        etc_folder = Folder(name='etc')
        etc_folder.save()

        # Oh look, it has an event!
        assert len(etc_folder.events) == 1

"""

import peewee

from flask import render_template_string
from flask_login import current_user
from playhouse.signals import (
    Model as SignalModel, post_save, pre_delete, pre_save
)
from werkzeug.utils import cached_property

from fleaker import DEFAULT_DICT, MISSING, db
from fleaker._compat import iteritems
from fleaker.peewee import JSONField

from .time import CreatedModifiedMixin


class EventMixin(SignalModel):
    """Peewee mixin that signifies that the model's activity should be tracked.

    Attributes:
        Meta.event_model (fleaker.peewee.EventStorageMixin):
            The storage model that will keep track of the Events.
        Meta.event_ready (bool):
            Should this model create events? This is helpful if your base of
            all models has the ``EventMixin``, but you'd rather not create
            events for a specific model that inherits from it.
        Meta.create_message (dict):
            This is an Event "mapping" that will be used to grab attributes
            from the  new model to save it in place.
    """
    _original = MISSING

    class Meta(object):
        event_ready = True
        create_message = DEFAULT_DICT
        delete_message = DEFAULT_DICT
        update_messages = DEFAULT_DICT

    def create_event_callback(self, event):
        """Overloadable callback function to manually modify the create event.

        By default, this does nothing, because the default behavior is defined
        elsewhere.

        Args:
            event (fleaker.peewee.EventMixin):
                The unsaved Event instance to modify by reference.
        """

    def update_event_callback(self, events):
        """Overloadable callback function to manually modify the update event.

        Event modification here should be designed as if you are getting
        multiple Events in a list, unline the create, which gets a single
        Event.

        Args:
            event (list[fleaker.peewee.EventStorageMixin]):
                The unsaved Event instance to modify by reference.
        """

    def delete_event_callback(self, event):
        """Overloadable callback function to manually modify the delete event.

        Args:
            event (list[fleaker.peewee.EventStorageMixin]):
                The unsaved Event instance to modify by reference.
        """

    def get_original(self):
        """Get the original instance of this instance before it's updated.

        Returns:
            fleaker.peewee.EventMixin:
                The original instance of the model.
        """
        pk_value = self._get_pk_value()

        if isinstance(pk_value, int) and not self._original:
            self._original = (
                self.select().where(self.__class__.id == pk_value).get()
            )

        return self._original

    def create_creation_event(self):
        """Parse the create message DSL to insert the data into the Event.

        Returns:
            fleaker.peewee.EventStorageMixin:
                A new Event instance with data put in it
        """
        event = self.create_audit_event(code='AUDIT_CREATE')

        if self._meta.create_message:
            event.body = self._meta.create_message['message']
            event.code = self._meta.create_message['code']
            event.meta = self.parse_meta(self._meta.create_message['meta'])

        self.create_event_callback(event)

        event.save()

        return event

    def create_update_event(self):
        """Parse the update messages DSL to insert the data into the Event.

        Returns:
            list[fleaker.peewee.EventStorageMixin]:
                All the events that were created for the update.
        """
        events = []

        for fields, rules in iteritems(self._meta.update_messages):
            if not isinstance(fields, (list, tuple, set)):
                fields = (fields,)

            changed = any([
                getattr(self, field) != getattr(self.get_original(), field)
                for field in fields
            ])

            if changed:
                event = self.create_audit_event(code=rules['code'])
                event.body = rules['message']
                event.meta = self.parse_meta(rules['meta'])
                events.append(event)

        self.update_event_callback(events)

        with db.database.atomic():
            for event in events:
                event.save()

        return events

    def create_deletion_event(self):
        """Parse the delete message DSL to insert data into the Event.

        Return:
            Event: The Event with the relevant information put in it.
        """
        event = self.create_audit_event(code='AUDIT_DELETE')

        if self._meta.delete_message:
            event.code = self._meta.delete_message['code']
            event.body = self._meta.delete_message['message']
            event.meta = self.parse_meta(self._meta.delete_message['meta'])

        self.delete_event_callback(event)

        event.save()

        return event

    def parse_meta(self, meta):
        """Parses the meta field in the message, copies it's keys into a new
        dict and replaces the values, which should be attribute paths relative
        to the passed in object, with the current value at the end of that
        path. This function will run recursively when it encounters other dicts
        inside the meta dict.

        Args:
            meta (dict):
                The dictionary of mappings to pull structure of the meta from.

        Returns:
            dict:
                A copy of the keys from the meta dict with the values pulled
                from the paths.
        """
        res = {}

        for key, val in meta.items():
            if not val:
                continue
            elif isinstance(val, dict):
                res[key] = self.parse_meta(val)
            elif val.startswith('current_user.'):
                res[key] = self.get_path_attribute(current_user, val)
            elif val.startswith('original.'):
                res[key] = self.get_path_attribute(self.get_original(), val)
            else:
                res[key] = self.get_path_attribute(self, val)

        return res

    @staticmethod
    def get_path_attribute(obj, path):
        """Given a path like `related_record.related_record2.id`, this method
        will be able to pull the value of ID from that object, returning None
        if it doesn't exist.

        Args:
            obj (fleaker.db.Model):
                The object to attempt to pull the value from
            path (str):
                The path to follow to pull the value from

        Returns:
            (int|str|None):
                The value at the end of the path. None if it doesn't exist at
                any point in the path.
        """
        # Strip out ignored keys passed in
        path = path.replace('original.', '').replace('current_user.', '')

        attr_parts = path.split('.')
        res = obj

        try:
            for part in attr_parts:
                try:
                    res = getattr(res, part)
                except AttributeError:
                    res = getattr(res.get(), part)

        except (peewee.DoesNotExist, AttributeError):
            return None

        return res

    def copy_foreign_keys(self, event):
        """Copies possible foreign key values from the object into the Event,
        skipping common keys like modified and created.

        Args:
            event (Event): The Event instance to copy the FKs into
            obj (fleaker.db.Model): The object to pull the values from
        """
        event_keys = set(event._meta.fields.keys())
        obj_keys = self._meta.fields.keys()
        matching_keys = event_keys.intersection(obj_keys)

        for key in matching_keys:
            # Skip created_by because that will always be the current_user
            # for the Event.
            if key == 'created_by':
                continue

            # Skip anything that isn't a FK
            if not isinstance(self._meta.fields[key], peewee.ForeignKeyField):
                continue

            setattr(event, key, getattr(self, key))

        # Attempt to set the obj's ID in the correct FK field on Event, if it
        # exists. If this conflicts with desired behavior, handle this in the
        # respective callback. This does rely on the FK matching the lower case
        # version of the class name and that the event isn't trying to delete
        # the current record, becuase that ends badly.
        possible_key = self.__class__.__name__.lower()

        if possible_key in event_keys and event.code != 'AUDIT_DELETE':
            setattr(event, possible_key, self)

    def create_audit_event(self, code='AUDIT'):
        """Creates a generic auditing Event logging the changes between saves
        and the initial data in creates.

        Kwargs:
            code (str): The code to set the new Event to.

        Returns:
            Event: A new event with relevant info inserted into it
        """
        event = self._meta.event_model(
            code=code,
            model=self.__class__.__name__,
        )

        # Use the logged in User, if possible
        if current_user:
            event.created_by = current_user.get_id()

        self.copy_foreign_keys(event)
        self.populate_audit_fields(event)

        return event

    def populate_audit_fields(self, event):
        """Populates the the audit JSON fields with raw data from the model, so
        all changes can be tracked and diffed.

        Args:
            event (Event): The Event instance to attach the data to
            instance (fleaker.db.Model): The newly created/updated model
        """
        event.updated = self._data
        event.original = self.get_original()._data


@pre_save(sender=EventMixin)
def get_original_before_save(sender, instance, created):
    """Event listener to get the original instance before it's saved."""
    if not instance._meta.event_ready or created:
        return

    instance.get_original()


@post_save(sender=EventMixin)
def post_save_event_listener(sender, instance, created):
    """Event listener to create creation and update events."""
    if not instance._meta.event_ready:
        return

    if created:
        instance.create_creation_event()
    else:
        instance.create_update_event()

    # Reset the original key
    instance._original = None


@pre_delete(sender=EventMixin)
def pre_delete_event_listener(sender, instance):
    """Event listener to create deletion events."""
    if not instance._meta.event_ready:
        return

    instance.create_deletion_event()


class EventStorageMixin(CreatedModifiedMixin):
    """Model that is used to store Events in the database.

    By default, this uses ``fleaker.peewee.CreatedModifiedMixin`` for
    timestamps, which uses Python's ``datetime`` module for timestamps. Support
    for Arrow and Pendulum are allowed, just add those mixins to the
    inheritance chain to override these defaults.

    Attributes:
        body (str):
            The message that represents the Event.
        code (str):
            The shortcode that represents the type of Event that happened.
        version (str|None):
            The version of this Event. Can be useful if the Event logic changes
            over time, but legacy Events must still work.
        meta (dict):
            A mapping of data that can be grabbed relatively from the instance
            creating the event.
        original (dict):
            A copy of all the data from the instance before it's saved.
        updated (dict):
            A copy of the newly saved data.
        model (str):
            The name of the model that the instance is.
    """
    body = peewee.TextField(null=True)
    code = peewee.CharField(max_length=255, null=False, default='AUDIT')
    version = peewee.CharField(max_length=255, null=True)
    meta = JSONField(null=True)
    original = JSONField(null=True)
    updated = JSONField(null=False)
    model = peewee.CharField(max_length=255, null=True)

    _default_event_codes = ['AUDIT_CREATE', 'AUDIT_DELETE', 'AUDIT_UPDATE']

    class Meta:
        event_codes = []

    @cached_property
    def formatted_message(self):
        """Method that will return the formatted message for the event.

        This formatting is done with Jinja and the template text is stored in
        the ``body`` attribute. The template is supplied the following
        variables, as well as the built in Flask ones:

        - ``event``: This is the event instance that this method belongs to.
        - ``meta``: This is a dictionary of cached values that have been stored
          when the event was created based upon the event's DSL.
        - ``original``: This is a dump of the instance before the instance was
          updated.
        - ``updated``: This is a dump of the instance after it was updated.
        - ``version``: This is the version of the event DSL.

        This property is cached because Jinja rendering is slower than raw
        Python string formatting.
        """
        return render_template_string(
            self.body,
            event=self,
            meta=self.meta,
            original=self.original,
            updated=self.updated,
            version=self.version,
        )

    @classmethod
    def event_codes(cls):
        event_codes = []
        event_codes.extend(cls._default_event_codes)
        event_codes.extend(cls._meta.event_codes)

        return event_codes


@pre_save(sender=EventStorageMixin)
def validate_event_type(sender, event, created):
    """Verify that the Event's code is a valid one."""
    if event.code not in sender.event_codes():
        raise ValueError("The Event.code '{}' is not a valid Event "
                         "code.".format(event.code))
