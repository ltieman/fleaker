# ~*~ coding: utf-8 ~*~
"""
fleaker.peewee.mixins.time.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Module that implements the base for time related Peewee mixins.

Example:
    To use these mixins, add the class to the model's inheritance chain.

    .. code-block:: python

        import peewee

        from fleaker import db
        from fleaker.peewee import ArchivedMixin

        class User(ArchivedMixin, db.Model):
            name = peewee.CharField()
            # This model is now setup to keep track of when a User is created,
            # modified, and has archiving capabilities.

        user = User(name="Bobby Tables")
        user.save()

        # Created is set upon the first save, but modified isn't set until the
        # first update. Archived isn't set until the record has been archived.
        assert user.created
        assert not user.modified
        assert not user.archived

        user.name = "Tom Hanks"
        user.save()

        # User was updated, so the modified timestamp is set.
        assert user.modified
        assert not user.archived

        # The ArchivedMixin provides methods to archive records.
        user.archive_instance()

        # Archiving will set the archived timestamp. It is guaranteed that the
        # archived timestamp and the modified will be equal upon that update.
        assert user.archived
        assert user.archived == user.modified

        # Records can be unarchived without any issues.
        user.unarchive_instance()

        # Which will just unset the archived timestamp.
        assert not user.archived

"""

from datetime import datetime

from peewee import DateTimeField
from playhouse.hybrid import hybrid_property
from playhouse.signals import Model as SignalModel, post_save, pre_save


class CreatedMixin(SignalModel):
    """Peewee mixin that provides record keeping for when a record was created.

    Attributes:
        created (datetime.datetime): The time at which this record was created.
        Meta.datetime (datetime.datetime): This is the datetime class that this
            mixin will use internally to set the datetimes. This library must
            have a ``utcnow`` method to work without additional work.
    """
    created = DateTimeField(null=False, default=datetime.utcnow)
    _cached_time = None

    class Meta:
        datetime = datetime

    def _get_cached_time(self):
        """Method that will allow for consistent modified and archived
        timestamps.

        Returns:
            self.Meta.datetime: This method will return a datetime that is
                compatible with the current class's datetime library.
        """
        if not self._cached_time:
            self._cached_time = self._meta.datetime.utcnow()

        return self._cached_time


class CreatedModifiedMixin(CreatedMixin):
    """Peewee mixin that provides record keeping for when a record was created
    and updated.

    Attributes:
        created (datetime.datetime): The time at which this record was created.
        modified (datetime.datetime): The time at which this record was
            modified. This will default to null on creation and will only be
            set after the first edit.
    """
    modified = DateTimeField(null=True)


class ArchivedMixin(CreatedModifiedMixin):
    """Peewee mixin that provides record keeping for when a record was created,
    modified, and archived.

    This mixin can be useful for when you want to display to a user a delete
    action but you don't actually want to delete the record.

    Attributes:
        created (datetime.datetime): The time at which this record was created.
        modified (datetime.datetime|None): The time at which this record was
            modified. This will default to null on creation and will only be
            set after the first edit.
        archived (datetime.datetime|None): The time at which this record was
            archived. This will default to ``None``.
        is_archived (bool | peewee.Clause): This is a hybrid property that
            allows for querying on archived records like you would on any other
            boolean field.
    """
    archived = DateTimeField(null=True)

    def archive_instance(self):
        """Method that will archive the instance.

        Returns:
            self: This method will return itself after a save has been done.
        """
        self.archived = self._get_cached_time()
        self.save()

        return self

    def unarchive_instance(self):
        """Method that will unarchive the instance.

        Returns:
            self: This method will return itself after a save has been done.
        """
        self.archived = None
        self.save()

        return self

    @hybrid_property
    def is_archived(self):
        """Hybrid property for querying for records that are archived."""
        return self.archived != None


@pre_save(sender=CreatedModifiedMixin)
def update_modified(sender, instance, created):
    """Peewee event listener to automatically set the modified timestamp.

    The modified timestamp will not be set on the initial creation of the
    record, only after it's first update.
    """
    if not created:
        instance.modified = instance._get_cached_time()


@post_save(sender=CreatedMixin)
def clear_cached_time(sender, instance, created):
    """Peewee event listener that will reset the cached time on the instance.

    This is needed so time is reflected accurately.
    """
    instance._cached_time = None
