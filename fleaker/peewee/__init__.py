"""
fleaker.peewee
~~~~~~~~~~~~~~

Module that provides helpful Peewee mixins and field types. The thought process
behind this module is to give a developer some powerful and unopinionated
classes to aid in building common functionality in an app.

Do you need to have search functionality in your app, but don't want to setup
and learn ElasticSearch? Give ``fleaker.peewee.SearchMixin`` a chance, it
should be passable for an MVP.

Or maybe you want to store unstructured data in your relational database that
is just used for presentation? I can promise you that using
``fleaker.peewee.JSONField`` is easier to use than MongoDB! (Note: Searching is
not supported in that field, so depend on it at your own risk.)

Everyone hates Python's ``datetime`` library. It's a known fact and it doesn't
seem like it's going to get any better. So why not use ``arrow`` or
``pendulum`` when using dates in your models? Our date mixins make them super
easy to use as well!
"""

from .fields import JSONField
from .model import Model
from .mixins import (
    FieldSignatureMixin, ArchivedMixin, CreatedMixin, CreatedModifiedMixin,
    SearchMixin, EventMixin, EventStorageMixin
)

try:
    import arrow
except ImportError:
    pass
else:
    from .fields import ArrowDateTimeField
    from .mixins import (ArrowArchivedMixin, ArrowCreatedMixin,
                         ArrowCreatedModifiedMixin)

try:
    import pendulum
except ImportError:
    pass
else:
    from .fields import PendulumDateTimeField
    from .mixins import (PendulumArchivedMixin, PendulumCreatedMixin,
                         PendulumCreatedModifiedMixin)
