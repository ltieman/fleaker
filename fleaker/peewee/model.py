"""
fleaker.peewee.model
~~~~~~~~~~~~~~~~~~~~

A base model for the Peewee ORM with sensible defaults.

The :class:`fleaker.peewee.Model` provided automatically hooks into the
database specified in the configuration provided to the application factory, so
no additional assignment is needed to make this work.

Furthermore, this model is configured to use Peewee's event system. In this
way, all of the models that extend off of this can hook into the event system
and do stuff before and after the record is created, modified, or deleted with
ease.

Example:
    To use this mixin, add this class to the model's inheritance chain::

    .. code-block:: python

        import peewee

        from fleaker.peewee import Model
        from playhouse.fields import PasswordField
        from playhouse.signals import post_save, pre_save

        class User(Model):
            email = peewee.CharField(max_length=100, null=False, unique=True)
            password = PasswordField(null=False, iterations=4)
            active = peewee.BooleanField(null=False, default=True)

            class Meta:
                integrity_error_msg = "User with email {email} already exists."

            @classmethod
            def base_query(cls):
                # This is the base query that you should use for all queries.
                # This is so that common logic can be contained to one location
                # and be enforced across all queries. If you need to get around
                # this, just use cls.select() directly.
                #
                # This will only query for active Users.
                return super(User, cls).base_query().where(cls.active == True)

        @pre_save(sender=User)
        def validate_email(sender, instance, created):
            # Ensure that the email is valid.
            if '@' not in instance.email:
                raise Exception("The email must be a valid email.")

        @post_save(sender=User)
        def send_welcome_email(sender, instance, created):
            # Send the user an email when they are created initially.
            if created:
                print('Sending welcome email to {}'.format(instance.email))

        # Create instances like you normally would with Peewee.
        # This save is going to trigger the welcome email being sent...
        user = user_model(email='jane.doe@example.com', password='password')
        user.save()

        # ...while this save will not send the email.
        user.password = 'new password'
        user.save()

        # Validation can easily be added with a pre_save handler
        try:
            user.email = 'not a valid email'
        except Exception as exc:
            assert str(exc) == 'The email must be a valid email.'

        # This model provides an easy way to update the instance of the model
        # from a dictionary. The idea workflow for this is to accept JSON
        # through an API and update the model in one line.
        data = {
            'email': 'jane.doe@example.org',
            'password': 'new password',
        }
        user.update_instance(data)

        # By providing a base query, we can automatically exclude inactive
        # Users. This allows for information hiding in all of your queries.
        user.active = False
        user.save()

        try:
            User.select(User.email == data['email']).get()
        except DoesNotExist:
            pass

"""

import peewee

from playhouse.signals import Model as SignalModel

from fleaker._compat import PY2, iteritems, exception_message
from fleaker.orm import _PEEWEE_EXT


class Model(SignalModel):
    """A Peewee base model with sensible defaults.

    This model will automatically hook into the database configured for the
    application. Furthermore, this model inherits from
    ``playhouse.signals.Model`` so all models that use this will be event
    ready.

    Attributes:
        Meta.integrity_error_msg (str):
            The friendly message that should be displayed when ``Model.save``
            catches ``peewee.IntegrityError``.
    """

    class Meta(object):
        database = _PEEWEE_EXT.database

    @classmethod
    def base_query(cls):
        """Method that should return the basic query that all queries will use.

        The default base query that just returns a blank ``SELECT`` statement.
        It should be overridden in child classes when ``JOIN`` or ``WHERE``
        will be needed for all queries.

        Returns:
            :py:class:`peewee.SelectQuery`:
                An unexecuted query with no logic applied.
        """
        return cls.select()

    @classmethod
    def get_by_id(cls, record_id, execute=True):
        """Return a single instance of the model queried by ID.

        Args:
            record_id (int): Integer representation of the ID to query on.

        Keyword Args:
            execute (bool, optional):
                Should this method execute the query or return a query object
                for further manipulation?

        Returns:
            cls | :py:class:`peewee.SelectQuery`:
                If ``execute`` is ``True``, the query is executed, otherwise
                a query is returned.

        Raises:
            :py:class:`peewee.DoesNotExist`:
                Raised if a record with that ID doesn't exist.
        """
        query = cls.base_query().where(cls.id == record_id)

        if execute:
            return query.get()

        return query

    def save(self, *args, **kwargs):
        """Save the instance's data.

        This method will also allow for modification of
        a :py:class:`peewee.IntegrityError`, if it is raised, to have
        a friendlier error message that can be set by the ``Meta`` class's
        ``integrity_error_msg`` variable.
        """
        try:
            super(Model, self).save(*args, **kwargs)
        except peewee.IntegrityError as exc:
            # Set the exceptions model and change the message to something
            # friendly, if possible.
            exc.model = self.__class__

            # Create the pretty message
            message = getattr(
                self._meta,
                'integrity_error_msg',
                exception_message(exc)
            ).format(**self._data)

            # Cache the original message
            exc.original_message = exception_message(exc)

            # This is the dumbest PY3 change.
            if PY2:
                exc.message = message
            else:
                exc.args = (message,)

            raise exc

    def update_instance(self, data):
        """Update a single record by id with the provided data.

        Args:
            data (dict): The new data to update the record with.

        Returns:
            self: This is an instance of itself with the updated data.

        Raises:
            AttributeError: This is raised if a key in the ``data`` isn't
                a field on the model.
        """
        for key, val in iteritems(data):
            if not hasattr(self, key):
                raise AttributeError(
                    "No field named {key} for model {model}".format(
                        key=key,
                        model=self.__class__.__name__
                    )
                )

            setattr(self, key, val)

        self.save()

        return self
