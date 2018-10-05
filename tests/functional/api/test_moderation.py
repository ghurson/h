# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

# String type for request/response headers and metadata in WSGI.
#
# Per PEP-3333, this is intentionally `str` under both Python 2 and 3, even
# though it has different meanings.
#
# See https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types
native_str = str


@pytest.mark.functional
class TestPutHide(object):

    def test_it_returns_http_204_for_group_admin_with_shared_annotation(self,
                                                                        app,
                                                                        group_annotation,
                                                                        user_with_token):
        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.put('/api/annotations/{id}/hide'.format(id=group_annotation.id),
                                                          headers=headers)

        # The creator of a group has moderation rights over the annotations in that group
        # and may moderate an annotation (IF the annotation is shared (not private))
        assert res.status_code == 204

    def test_it_is_idempotent(self, app, group_annotation, user_with_token):
        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        app.put('/api/annotations/{id}/hide'.format(id=group_annotation.id),
                                                          headers=headers)
        res = app.put('/api/annotations/{id}/hide'.format(id=group_annotation.id),
                                                          headers=headers)

        assert res.status_code == 204
        assert group_annotation.moderation is not None

    def test_it_returns_http_404_if_creator_not_admin_of_annotation_group(self,
                                                                          app,
                                                                          world_annotation,
                                                                          user_with_token):
        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.put('/api/annotations/{id}/hide'.format(id=world_annotation.id),
                                                          headers=headers,
                                                          expect_errors=True)

        # The current user created (owns) this (shared) annotation
        # but the current user does not have `moderate` permission on the
        # annotation's group, thus this is an authz failure that should be
        # represented by a 404 (to not leak existence info)
        assert res.status_code == 404

    def test_it_returns_http_404_if_no_authn(self,
                                             app,
                                             group_annotation):

        res = app.put('/api/annotations/{id}/hide'.format(id=group_annotation.id),
                                                          expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_http_405_if_own_annotation_is_private(self,
                                                              app,
                                                              private_annotation,
                                                              user_with_token):

        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.put('/api/annotations/{id}/hide'.format(id=private_annotation.id),
                                                          headers=headers,
                                                          expect_errors=True)

        # If an annotation is private, its creator has the permission to
        # ``moderate`` it and thus will pass authz for the view.
        # However, moderating a private annotation is nonsensical, so the
        # view will raise an HTTP 405
        assert res.status_code == 405
        assert res.json['reason'] == 'Private annotations cannot be moderated'


@pytest.mark.functional
class TestDeleteHide(object):
    """See ``TestPutHide`` for explanation of access/authz and logic"""

    def test_it_returns_http_204_for_group_admin_with_shared_annotation(self,
                                                                        app,
                                                                        group_annotation,
                                                                        user_with_token):
        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.delete('/api/annotations/{id}/hide'.format(id=group_annotation.id),
                                                             headers=headers)

        assert res.status_code == 204

    def test_it_is_idempotent(self, app, group_annotation, user_with_token):
        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        app.delete('/api/annotations/{id}/hide'.format(id=group_annotation.id),
                                                       headers=headers)
        res = app.delete('/api/annotations/{id}/hide'.format(id=group_annotation.id),
                                                             headers=headers)

        assert res.status_code == 204
        assert group_annotation.moderation is None

    def test_it_returns_http_404_if_creator_not_admin_of_annotation_group(self,
                                                                          app,
                                                                          world_annotation,
                                                                          user_with_token):
        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.delete('/api/annotations/{id}/hide'.format(id=world_annotation.id),
                                                             headers=headers,
                                                             expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_http_404_if_no_authn(self,
                                             app,
                                             group_annotation):

        res = app.delete('/api/annotations/{id}/hide'.format(id=group_annotation.id),
                                                             expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_http_405_if_own_annotation_is_private(self,
                                                              app,
                                                              private_annotation,
                                                              user_with_token):

        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.delete('/api/annotations/{id}/hide'.format(id=private_annotation.id),
                                                             headers=headers,
                                                             expect_errors=True)

        # If an annotation is private, its creator has the permission to
        # ``moderate`` it and thus will pass authz for the view.
        # However, moderating a private annotation is nonsensical, so the
        # view will raise an HTTP 405
        assert res.status_code == 405
        assert res.json['reason'] == 'Private annotations cannot be moderated'


@pytest.fixture
def user(db_session, factories):
    user = factories.User()
    db_session.commit()
    return user


@pytest.fixture
def group(user, db_session, factories):
    group = factories.Group(creator=user)
    db_session.commit()
    return group


@pytest.fixture
def world_annotation(user, db_session, factories):
    ann = factories.Annotation(userid=user.userid,
                               groupid='__world__',
                               shared=True)
    db_session.commit()
    return ann


@pytest.fixture
def private_annotation(user, db_session, factories):
    ann = factories.Annotation(userid=user.userid,
                               groupid='__world__',
                               shared=False)
    db_session.commit()
    return ann


@pytest.fixture
def group_annotation(user, group, db_session, factories):
    ann = factories.Annotation(userid='acct:someone@example.com',
                               groupid=group.pubid,
                               shared=True)
    db_session.commit()
    return ann


@pytest.fixture
def private_group_annotation(group, db_session, factories):
    ann = factories.Annotation(userid='acct:someone@example.com',
                               groupid=group.pubid,
                               shared=False)
    db_session.commit()
    return ann


@pytest.fixture
def owned_private_group_annotation(user, group, db_session, factories):
    ann = factories.Annotation(userid=user.userid,
                               groupid=group.pubid,
                               shared=False)
    db_session.commit()
    return ann


@pytest.fixture
def user_with_token(user, db_session, factories):
    token = factories.DeveloperToken(userid=user.userid)
    db_session.add(token)
    db_session.commit()
    return (user, token)
