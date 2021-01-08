# Copyright 2017-2021 Manheim / Cox Automotive
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest.mock import patch, call, DEFAULT

from manheim_c7n_tools.notifyonly import NotifyOnlyPolicy
from c7n.tags import DEFAULT_TAG

pbm = 'manheim_c7n_tools.notifyonly'
pb = f'{pbm}.NotifyOnlyPolicy'


class TestAsNotifyOnly:

    def test_all(self):
        policy = {
            'foo': 'bar',
            'notify_only': True,
            'baz': 'blam',
            'comment': 'commentVal',
            'comments': 'commentsVal',
            'description': 'descriptionVal',
            'tags': ['my', 'tags'],
            'actions': ['some', 'actions']
        }
        with patch(f'{pb}._fix_actions') as mock_fa:
            mock_fa.return_value = ['updated', 'actions']
            res = NotifyOnlyPolicy.as_notify_only(policy)
        assert res == {
            'foo': 'bar',
            'baz': 'blam',
            'comment': 'NOTIFY ONLY: commentVal',
            'comments': 'NOTIFY ONLY: commentsVal',
            'description': 'NOTIFY ONLY: descriptionVal',
            'tags': ['my', 'tags', 'notify-only'],
            'actions': ['updated', 'actions']
        }
        assert mock_fa.mock_calls == [
            call(['some', 'actions'])
        ]

    def test_empty_policy(self):
        policy = {
            'foo': 'bar',
            'baz': 'blam',
        }
        with patch(f'{pb}._fix_actions') as mock_fa:
            mock_fa.return_value = ['updated', 'actions']
            res = NotifyOnlyPolicy.as_notify_only(policy)
        assert res == {
            'foo': 'bar',
            'baz': 'blam',
        }
        assert mock_fa.mock_calls == []


class TestFixComment:

    def test_simple(self):
        assert NotifyOnlyPolicy._fix_comment('foo') == 'NOTIFY ONLY: foo'


class TestFixTags:

    def test_simple(self):
        assert NotifyOnlyPolicy._fix_tags(['foo']) == ['foo', 'notify-only']


class TestFixActions:

    def test_all(self):
        actions = [
            'something',
            {'type': 'foo'},
            {'type': 'notify'},
            {'type': 'mark'},
            {'type': 'tag'},
            {'type': 'mark-for-op'},
            {'type': 'remove-tag'},
            {'type': 'unmark'},
            {'type': 'untag'},
            {'type': 'bar'},
        ]
        with patch.multiple(
            pb,
            _fix_tag_action=DEFAULT,
            _fix_mark_for_op_action=DEFAULT,
            _fix_untag_action=DEFAULT,
        ) as mocks:
            mocks['_fix_tag_action'].return_value = {'fixed': 'tag'}
            mocks['_fix_mark_for_op_action'].return_value = {'fixed': 'op'}
            mocks['_fix_untag_action'].return_value = {'fixed': 'untag'}
            res = NotifyOnlyPolicy._fix_actions(actions)
        assert res == [
            {'type': 'notify'},
            {'fixed': 'tag'},
            {'fixed': 'tag'},
            {'fixed': 'op'},
            {'fixed': 'untag'},
            {'fixed': 'untag'},
            {'fixed': 'untag'}
        ]
        assert mocks['_fix_tag_action'].mock_calls == [
            call({'type': 'mark'}),
            call({'type': 'tag'})
        ]
        assert mocks['_fix_mark_for_op_action'].mock_calls == [
            call({'type': 'mark-for-op'})
        ]
        assert mocks['_fix_untag_action'].mock_calls == [
            call({'type': 'remove-tag'}),
            call({'type': 'unmark'}),
            call({'type': 'untag'}),
        ]


class TestFixTagAction:

    def test_tag(self):
        policy = {
            'action': 'mark',
            'tag': 'foo',
            'value': 'bar'
        }
        assert NotifyOnlyPolicy._fix_tag_action(policy) == {
            'action': 'mark',
            'tag': 'foo-notify-only',
            'value': 'bar'
        }

    def test_key(self):
        policy = {
            'action': 'mark',
            'key': 'foo',
            'value': 'bar'
        }
        assert NotifyOnlyPolicy._fix_tag_action(policy) == {
            'action': 'mark',
            'key': 'foo-notify-only',
            'value': 'bar'
        }

    def test_tags(self):
        policy = {
            'action': 'mark',
            'tags': {'foo': 'bar', 'baz': 'blam'}
        }
        assert NotifyOnlyPolicy._fix_tag_action(policy) == {
            'action': 'mark',
            'tags': {'foo-notify-only': 'bar', 'baz-notify-only': 'blam'}
        }

    def test_default_tag(self):
        policy = {
            'action': 'mark',
            'value': 'bar'
        }
        assert NotifyOnlyPolicy._fix_tag_action(policy) == {
            'action': 'mark',
            'tag': f'{DEFAULT_TAG}-notify-only',
            'value': 'bar'
        }


class TestFixMarkForOpAction:

    def test_tag_present(self):
        policy = {
            'action': 'mark-for-op',
            'op': 'foo',
            'tag': 'mytag',
            'days': 7
        }
        assert NotifyOnlyPolicy._fix_mark_for_op_action(policy) == {
            'action': 'mark-for-op',
            'op': 'foo',
            'tag': 'mytag-notify-only',
            'days': 7
        }

    def test_tag_not_present(self):
        policy = {
            'action': 'mark-for-op',
            'op': 'foo',
            'days': 7
        }
        assert NotifyOnlyPolicy._fix_mark_for_op_action(policy) == {
            'action': 'mark-for-op',
            'op': 'foo',
            'tag': f'{DEFAULT_TAG}-notify-only',
            'days': 7
        }


class TestFixUntagAction:

    def test_simple(self):
        assert NotifyOnlyPolicy._fix_untag_action({
            'tags': ['foo', 'bar'],
            'baz': 'blam',
            'action': 'untag'
        }) == {
            'tags': ['foo-notify-only', 'bar-notify-only'],
            'baz': 'blam',
            'action': 'untag'
        }
