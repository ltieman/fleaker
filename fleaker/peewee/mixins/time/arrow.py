# ~*~ coding: utf-8 ~*~
"""
fleaker.peewee.mixins.time.arrow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Module that implements mixins that provide timestamp accounting for models. The
only difference between this model and
:py:class:`fleaker.peewee.mixins.time.base` is that the timestamps are
:py:class:`arrow.Arrow` objects.

Example:
    To use these mixins, add the class to the model's inheritance chain.

    .. code-block:: python

        import peewee

        from fleaker import db
        from fleaker.peewee import ArrowArchivedMixin

        class User(ArrowArchivedMixin, db.Model):
            name = peewee.CharField(max_length=255)
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

from __future__ import absolute_import

import arrow

from fleaker.peewee.fields import ArrowDateTimeField

from .base import CreatedMixin, CreatedModifiedMixin, ArchivedMixin


class ArrowCreatedMixin(CreatedMixin):
    """Peewee mixin that provides record keeping for when a record was created.

    This mixin will provide the dates it provides with :py:class:`arrow.Arrow`
    instead of :py:mod:`datetime.datetime`.

    Attributes:
        created (arrow.Arrow): The time at which this record was created.
    """
    created = ArrowDateTimeField(null=False, default=arrow.utcnow)

    class Meta(object):
        datetime = arrow


class ArrowCreatedModifiedMixin(ArrowCreatedMixin, CreatedModifiedMixin):
    """Peewee mixin that provides record keeping for when a record is created
    and modified.

    This mixin will provide the dates it provides with :py:class:`arrow.Arrow`
    instead of :py:mod:`datetime.datetime`.

    Attributes:
        created (arrow.Arrow): The time at which this record was created.
        modified (arrow.Arrow | None): The time at which this record was
            modified. This will default to null on creation and will only be
            set after the first edit.
    """
    modified = ArrowDateTimeField(null=True)


class ArrowArchivedMixin(ArrowCreatedModifiedMixin, ArchivedMixin):
    """Peewee mixin that provides record keeping for when a record was created,
    modified, and archived.

    This mixin can be useful for when you want to display to a user a delete
    action but you don't actually want to delete the record.

    This mixin will provide the dates it provides with :py:class:`arrow.Arrow`
    instead of :py:mod:`datetime.datetime`.

    Attributes:
        created (arrow.Arrow): The time at which this record was created.
        modified (arrow.Arrow | None):
            The time at which this record was modified. This will default to
            null on creation and will only be set after the first edit.
        archived (arrow.Arrow | None): The time at which this record was
            archived. This will default to ``None``.
        is_archived (bool | peewee.Clause): This is a hybrid property that
            allows for querying on archived records like you would on any other
            boolean field.
    """
    archived = ArrowDateTimeField(null=True)
