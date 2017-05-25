"""Unit tests for the SearchMixin."""

import peewee
import pytest

from fleaker.peewee import SearchMixin


@pytest.fixture
def post_model(database):
    """Fixture that provides a fixture for the Post model."""
    class Post(SearchMixin, database.Model):
        title = peewee.CharField(max_length=255, null=False)
        body = peewee.TextField(null=False, default='')

    Post._meta.database = database.database
    Post.create_table(True)

    return Post


def test_search_fields_must_be_provided(post_model):
    """Ensure that search fields need to be set."""
    # Nothing is defined to search on, so error out
    with pytest.raises(AttributeError):
        post_model.search('hello')

    # If fields are provided, return a query
    assert isinstance(post_model.search('hello', fields=('body',)),
                      peewee.SelectQuery)


def test_search_mixin_functionality(post_model):
    """Ensure that the SearchMixin works as expected."""
    # Add the default search fields
    post_model._meta.search_fields = ('title', 'body')

    # Create some Posts
    post_model.insert_many([
        {'title': 'Welcome!', 'body': 'Content'},
        {'title': 'Content is hard to write.', 'body': 'I am lazy.'},
        {'title': 'Hacked!', 'body': 'Some malcontent hacked this site!'},
    ]).execute()

    # Because all the Posts have the word 'content' in them, a search
    # should return all the posts.
    content_query = post_model.search('Content')

    assert content_query.count() == post_model.select().count() == 3

    # The search query is ordered by relevance in this order:
    #
    # 1. Straight equality (``posts.body = 'Content'``)
    # 2. Right hand ``LIKE`` (``posts.body LIKE 'Content%')
    # 3. Substring ``LIKE`` (``posts.content LIKE %Content%``)
    #
    # The query's search term is applied to the query case insensitively.
    # It should also be noted that matches for title will be ordered above
    # matches for content because of the ordering in Meta.search_fields.
    content_posts = list(content_query)

    # Only Post with 'Content' in the title.
    assert content_posts[0].title == 'Content is hard to write.'

    # Post.body was an exact match for 'Content'
    assert content_posts[1].title == 'Welcome!'

    # Post.body had the word 'Content' in there somewhere.
    assert content_posts[2].title == 'Hacked!'

    # The search method can overload the searched fields by providing it's
    # own list.
    hacked_search = post_model.search('hacked', fields=('title',))

    assert hacked_search.count() == 1
