# ~*~ coding: utf-8 ~*~
"""
fleaker.peewee.mixins.field_signature
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Module that implements a mixin that can be used for unique indexes across
multiple columns, where at least one of the columns is nullable.

It should be noted that because of Peewee's simplistic signal system, the
signature will only be updated when ``peewee.Model.save`` is called and will
not work with ``UPDATE`` queries.

Because no Fleaker mixins define migrations or create columns automatically,
it is left to the developer to add this column to the model in whatever system
they are using. The SQL needed for this column is roughly equivalent to the
following SQL (assuming the table is called ``folders`` like it is below):

    .. code-block:: sql

        ALTER TABLE `folders`
            ADD CHAR(40) `signature` NULL,
            ADD CONSTRAINT `uc_folders_signature` UNIQUE (`signature`);

Example:
    To use this mixin, add the class to the model's inheritance chain.

    .. code-block:: python

        import peewee

        from fleaker import db
        from fleaker.peewee import ArchivedMixin, FieldSignatureMixin

        class Folder(FieldSignatureMixin, ArchivedMixin, db.Model):
            # This class represents a Folder in a file system. Two Folders with
            # the same name cannot exist in the same Folder. If the Folder has
            # no Parent Folder, it exists in the top level of the file system.
            name = peewee.CharField(max_length=255, null=False)
            parent_folder = peewee.ForeignKeyField('self', null=True)

            class Meta:
                signature_fields = ('name', 'parent_folder')

        # Create a top level Folder
        etc_folder = Folder(name='etc')
        etc_folder.save()

        # Folder now has a signature
        assert etc_folder.signature

        # Two Folders with the same name cannot exist in the same parent Folder
        try:
            Folder(name='etc').save()
        except peewee.IntegrityError:
            assert True
        else:
            assert False

        # The signature of the instance will be nulled out when archived so
        # that future records can be active with the same signature.
        etc_folder.archive_instance()
        assert folder.signature is None

"""

from hashlib import sha1

from peewee import FixedCharField
from playhouse.signals import Model as SignalModel, pre_save

from fleaker._compat import text_type


class FieldSignatureMixin(SignalModel):
    """Mixin that provides reliable multi column unique indexes.

    This is done by computing the combined values of specified columns into a
    SHA1 hash that can have a unique index applied to it. This value will be
    stored in a field named ``signature``. When a field is archived, this hash
    is set to null to prevent issues going forward.

    This mixin is needed because MySQL cannot have a unique index across
    multiple columns if one or more of the columns are nullable. They have
    marked this issues a WONTFIX because MySQL is a fickle beast.

    Attributes:
        signature (str|None): This is a ``sha1`` hash computed from the fields
            defined in the ``Meta.signature_fields``. This is nulled out if the
            instance is archived.
        Meta.signature_fields (tuple[str]): The names of the fields to factor
            into the computed signature.
    """
    # This is where the signature is stored
    signature = FixedCharField(max_length=40, null=True, unique=True)

    # This is an overridable list of fields that should be used to compose the
    # hash, in order (not that order matters when composing a hash, as long as
    # it stays consistent).
    class Meta:
        signature_fields = ()

    def update_signature(self):
        """Update the signature field by hashing the ``signature_fields``.

        Raises:
            AttributeError: This is raised if ``Meta.signature_fields`` has no
                values in it or if a field in there is not a field on the
                model.
        """
        if not self._meta.signature_fields:
            raise AttributeError(
                "No fields defined in {}.Meta.signature_fields. Please define "
                "at least one.".format(type(self).__name__)
            )

        # If the field is archived, unset the signature so records in the
        # future can have this value.
        if getattr(self, 'archived', False):
            self.signature = None
            return

        # Otherwise, combine the values of the fields together and SHA1 them
        computed = [getattr(self, value) or ' '
                    for value in self._meta.signature_fields]
        computed = ''.join([text_type(value) for value in computed])

        # If computed is a falsey value, that means all the fields were
        # None or blank and that will lead to some pain.
        if computed:
            self.signature = sha1(computed.encode('utf-8')).hexdigest()


@pre_save(sender=FieldSignatureMixin)
def update_signature(sender, instance, **kwargs):
    """Peewee event listener that will update the unique hash for the field
    before saving the record.
    """
    instance.update_signature()
