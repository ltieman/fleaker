"""Unit tests for the base Peewee Model."""

import peewee
import pytest

from playhouse.fields import PasswordField
from playhouse.signals import post_save, pre_save

from fleaker._compat import exception_message
from fleaker.peewee import Model
from tests.constants import SQLITE_DATABASE_NAME


@pytest.fixture
def user_model(database):
    """Fixture that provides a simple User model."""
    class User(Model):
        email = peewee.CharField(max_length=100, null=False, unique=True)
        password = PasswordField(null=False, iterations=4)
        active = peewee.BooleanField(null=False, default=True)

        @classmethod
        def base_query(cls):
            # Only query for active Users
            return super(User, cls).base_query().where(cls.active == True)

    try:
        @pre_save(sender=User)
        def validate_email(sender, instance, created):
            # Ensure that the email is valid.
            assert '@' in instance.email

        @post_save(sender=User)
        def send_welcome_email(sender, instance, created):
            # Send the user an email when they are created initially.
            if created:
                print('Sending welcome email to {}'.format(instance.email))
    except ValueError:
        # This gets hit because you can't connect an event listener more than
        # once and for some reason this fixture is sticking around.
        pass

    User.create_table(True)

    yield User


def test_create_model(user_model):
    """Ensure that a Model instance can be created sanely."""
    email = 'john.doe@example.com'
    password = 'password'

    user = user_model(email=email, password=password)
    user.save()

    # Make sure that the model is using the database specified in the config.
    assert user_model._meta.database.database == SQLITE_DATABASE_NAME

    # Query the user to get it fresh
    queried_user = user_model.get_by_id(user.id)

    # Make sure data checks out.
    assert queried_user.email == 'john.doe@example.com'
    assert queried_user.password != password
    assert queried_user.password.check_password('password')


def test_update_model(user_model):
    """Ensure that a Model instance can be updated sanely."""
    user = user_model(email='jane.doe@example.com', password='password')
    user.save()

    # Now, let's update the user.
    data = {
        'email': 'jane.doe@example.org',
        'password': 'new_password'
    }
    user.update_instance(data)

    # Get a fresh copy of the user to make sure it updated.
    fresh_user = user_model.get_by_id(user.id)

    assert fresh_user.email == data['email']
    assert fresh_user.password.check_password(data['password'])

    # Make sure that only fields on the model can be updated
    with pytest.raises(AttributeError):
        fresh_user.update_instance({'not': 'present'})


def test_get_model(user_model):
    """Ensure that a Model can be fetched by ID."""
    # This user will be fetchable because they are active my default
    active_user = user_model(
        email='bob.blah@example.com',
        password='password',
    )
    active_user.save()

    assert active_user == user_model.get_by_id(active_user.id)
    assert isinstance(user_model.get_by_id(active_user.id, execute=False),
                      peewee.SelectQuery)

    # This user will not be fetchable by ID because of the base_query
    inactive_user = user_model(
        email='lana.landsman@example.com',
        password='password',
        active=False,
    )
    inactive_user.save()

    with pytest.raises(peewee.DoesNotExist):
        user_model.get_by_id(inactive_user.id)
