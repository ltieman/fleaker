"""Unit tests for the Event mixin."""

import peewee
import pytest

from flask_login import UserMixin, current_user, login_user

from fleaker.peewee import EventStorageMixin, EventMixin

from .conftest import login_manager


class User(EventMixin, UserMixin):
    """A user interacting with a file system."""
    name = peewee.CharField(max_length=255, null=False)

    class Meta:
        update_messages = {
            'name': {
                'code': 'USER_RENAMED',
                'message': ("{{original.user.name}} renamed themselves to "
                            "{{meta.user.user_name}}"),
                'meta': {
                    'user': {
                        'og_name': 'original.name',
                        'new_name': 'current_user.name',
                    },
                },
            }
        }


@login_manager.user_loader
def load_user(user_id):
    return User.select().where(User.id == user_id).get()


class Session(EventMixin):
    """Model to store a User's logins."""
    user = peewee.ForeignKeyField(User, null=False, related_name='sessions')

    class Meta:
        event_ready = False


class Folder(EventMixin):
    """A folder in a file system."""
    created_by = peewee.ForeignKeyField(User, null=False)
    name = peewee.CharField(max_length=255)
    parent_folder = peewee.ForeignKeyField('self', null=True)

    class Meta:
        create_message = {
            'code': 'FOLDER_CREATED',
            'message': (
                "{{event.created_by.name}} created {{meta.folder.text}} "
                "in {{meta.parent.text}}."
            ),
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
        update_messages = {
            'name': {
                'code': 'FOLDER_RENAMED',
                'message': ("{{event.created_by.name}} renamed "
                            "{{meta.og_folder.text}} to "
                            "{{meta.folder.text}}."),
                'meta': {
                    'og_folder': {
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
    """A file in a file system."""
    created_by = peewee.ForeignKeyField(User, null=False)
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
                    'og_file': {
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
    """Model that tracks Events."""
    folder = peewee.ForeignKeyField(Folder, null=True, related_name='events')
    file = peewee.ForeignKeyField(File, null=True, related_name='events')
    session = peewee.ForeignKeyField(Session, null=True, related_name='events')
    created_by = peewee.ForeignKeyField(User, null=True, related_name='events')

    class Meta:
        order_by = ('-id',)
        event_codes = (
            'FOLDER_CREATED',
            'FOLDER_DELETED',
            'FOLDER_RENAMED',
            'FOLDER_MOVED',
            'FILE_CREATED',
            'FILE_DELETED',
            'FILE_RENAMED',
            'FILE_MOVED',
            'USER_RENAMED',
        )


@pytest.fixture
def models(database):
    """Fixture that creates the models in the database."""
    for model in (User, Folder, File, Event, Session):
        model._meta.database = database.database
        model._meta.event_model = Event
        model.create_table(True)

    return None


@pytest.fixture
def logged_in_user(models):
    """Fixture that will setup the models, create a user, and log them in."""
    user = User(name='Tom Hanks')
    user.save()

    login_user(user)

    Session(user=user).save()

    return user


def test_folder_creation_event(logged_in_user):
    """Ensure that the Folder creation event succeeds."""
    usr_folder = Folder(name='usr', created_by=current_user.id)
    usr_folder.save()

    assert len(usr_folder.events) == 1
    event = usr_folder.events.get()

    assert event.code == 'FOLDER_CREATED'
    assert event.created_by == logged_in_user
    assert event.folder == usr_folder
    assert event.file is None
    assert isinstance(event.meta, dict)
    assert event.original
    assert isinstance(event.original, dict)
    assert event.updated
    assert isinstance(event.updated, dict)
    assert event.formatted_message == "Tom Hanks created usr in the root."


def test_folder_update_event(logged_in_user):
    """Ensure that the Folder update event succeeds."""
    # Create a Folder
    etc_folder = Folder(name='ETC', created_by=current_user.id)
    etc_folder.save()

    # Hey let's move that Folder it a lower case setup
    etc_folder.name = 'etc'
    etc_folder.save()

    # Two events, one for the creation, another for the movement.
    assert etc_folder.events.count() == 2

    # Since the IDs are in descending order, I can guarantee that the movement
    # event is first.
    event = etc_folder.events.get()

    assert event.code == 'FOLDER_RENAMED'
    assert event.folder == etc_folder
    assert event.created_by == logged_in_user
    assert event.file is None
    assert event.updated['id'] == event.original['id'] == etc_folder.id
    assert event.updated['name'] == 'etc'
    assert event.original['name'] == 'ETC'
    assert event.formatted_message == "Tom Hanks renamed ETC to etc."


def test_folder_deletion_event(logged_in_user):
    """Ensure that the Folder deletion event succeeds."""
    # Create a Folder
    var_folder = Folder(name='var', created_by=current_user.id)
    var_folder.save()

    # Delete that Folder
    var_folder.delete_instance()

    # Get the deletion Event
    event = Event.select().where(Event.code == 'FOLDER_DELETED').get()

    assert event.created_by == logged_in_user
    assert event.folder is None
    assert event.file is None
    assert event.updated['id'] == var_folder.id
    assert event.updated['name'] == 'var'
    assert event.formatted_message == "Tom Hanks deleted var from the root."


def test_event_codes_must_be_valid(logged_in_user):
    """Ensure that only valid Event codes are allowed."""
    with pytest.raises(ValueError):
        Event(code='THIS_IS_NOT_VALID', original={}).save()


def test_non_event_ready_models_are_logged(logged_in_user):
    """Ensure that event_ready = False is respected."""
    session = logged_in_user.sessions.get()
    assert session.events.count() == 0

    session.save()
    assert session.events.count() == 0

    session.delete_instance()
    assert Event.select().where(Event.session != None).count() == 0  # noqa


def test_file_added_to_folder(logged_in_user):
    """Ensure that meta FKs are copied properly."""
    # Create the etc folder.
    etc_folder = Folder(name='etc', created_by=current_user.id)
    etc_folder.save()

    # Add the passwd file to etc
    passwd_file = File(
        name='passwd',
        folder=etc_folder,
        created_by=current_user.id
    )
    passwd_file.save()

    assert passwd_file.events.count() == 1

    event = passwd_file.events.get()
    assert event.code == 'FILE_CREATED'
    assert event.formatted_message == 'Tom Hanks created passwd in etc.'
    assert event.folder == etc_folder
    assert event.file == passwd_file


def test_rename_user(logged_in_user):
    """Ensure the data from current_user is grabbed."""
    logged_in_user.name = 'Nick Cage'
    logged_in_user.save()

    assert logged_in_user.events.count() == 1

    event = logged_in_user.events.get()
    assert event.code == 'USER_RENAMED'
    assert event.meta['user']['og_name'] == 'Tom Hanks'
    assert event.meta['user']['new_name'] == 'Nick Cage'
