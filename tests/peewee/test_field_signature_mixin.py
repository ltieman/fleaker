# ~*~ coding: utf-8 ~*~
"""Unit tests for the FieldSignatureMixin."""

import pytest

peewee = pytest.importorskip('peewee')

from fleaker.peewee import ArchivedMixin, FieldSignatureMixin


@pytest.fixture
def folder_model(database):
    class Folder(FieldSignatureMixin, ArchivedMixin):
        # This class represents a Folder in a file system. Two Folders with
        # the same name cannot exist in the same Folder. If the Folder has
        # no Parent Folder, it exists in the top level of the file system.
        name = peewee.CharField(max_length=255, null=False)
        parent_folder = peewee.ForeignKeyField('self', null=True)

        class Meta:
            signature_fields = ('name', 'parent_folder')

    Folder._meta.database = database.database
    Folder.create_table(True)

    return Folder


def test_signature_fields_must_be_set(folder_model):
    """
    Ensure that an exception is raised if the signature_fields aren't set.
    """
    folder_model._meta.signature_fields = ()

    with pytest.raises(AttributeError):
        folder_model(name='etc').save()


def test_signature_functionality(folder_model):
    """Ensure that the FieldSignatureMixin works as expected."""
    # Create a Folder named 'etc' in the root of the file system.
    etc_folder = folder_model(name='etc')
    etc_folder.save()

    assert etc_folder.signature
    assert len(etc_folder.signature) == 40

    # No other Folders in the root may be named 'etc
    with pytest.raises(peewee.IntegrityError):
        folder_model(name='etc').save()

    # Let's test this with a child Folder of 'etc'
    apt_folder = folder_model(name='apt', parent_folder=etc_folder)
    apt_folder.save()

    assert apt_folder.signature
    assert len(apt_folder.signature) == 40

    # Can't have another named 'apt' in 'etc'
    with pytest.raises(peewee.IntegrityError):
        folder_model(name='apt', parent_folder=etc_folder).save()

    # If a Folder is archived, it's signature is nulled out
    etc_folder.archive_instance()

    assert etc_folder.signature is None
