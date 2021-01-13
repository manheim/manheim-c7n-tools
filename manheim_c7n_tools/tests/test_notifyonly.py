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


class TestInit:

    def test_simple(self):
        with patch(f'{pb}._process') as m_process:
            m_process.return_value = {'fixed': 'policy'}
            cls = NotifyOnlyPolicy({'my': 'policy'})
        assert cls._original == {'my': 'policy'}
        assert cls._fixed == {'fixed': 'policy'}
        assert cls._mark_for_op_tags == []
        assert m_process.mock_calls == [
            call({'my': 'policy'})
        ]


class NotifyOnlyTester:

    def setup(self):
        self.policy = {}
        with patch(f'{pb}._process') as m_process:
            m_process.return_value = {}
            self.cls = NotifyOnlyPolicy(self.policy)


class TestAsNotifyOnly(NotifyOnlyTester):

    def test_simple(self):
        self.cls._fixed = {'foo': 'bar'}
        assert self.cls.as_notify_only() == {'foo': 'bar'}


class TestProcess(NotifyOnlyTester):

    def test_all(self):
        policy = {
            'foo': 'bar',
            'notify_only': True,
            'baz': 'blam',
            'comment': 'commentVal',
            'comments': 'commentsVal',
            'description': 'descriptionVal',
            'tags': ['my', 'tags'],
            'actions': ['some', 'actions'],
            'filters': ['my-filters']
        }
        with patch(f'{pb}._fix_actions', autospec=True) as mock_fa:
            mock_fa.return_value = ['updated', 'actions']
            with patch(f'{pb}._fix_filters', autospec=True) as mock_ff:
                mock_ff.return_value = ['fixed', 'filters']
                res = self.cls._process(policy)
        assert res == {
            'foo': 'bar',
            'baz': 'blam',
            'comment': 'NOTIFY ONLY: commentVal',
            'comments': 'NOTIFY ONLY: commentsVal',
            'description': 'NOTIFY ONLY: descriptionVal',
            'tags': ['my', 'tags', 'notify-only'],
            'actions': ['updated', 'actions'],
            'filters': ['fixed', 'filters']
        }
        assert mock_fa.mock_calls == [
            call(self.cls, ['some', 'actions'])
        ]
        assert mock_ff.mock_calls == [
            call(self.cls, ['my-filters'])
        ]

    def test_empty_policy(self):
        policy = {
            'foo': 'bar',
            'baz': 'blam',
        }
        with patch(f'{pb}._fix_actions', autospec=True) as mock_fa:
            mock_fa.return_value = ['updated', 'actions']
            with patch(f'{pb}._fix_filters', autospec=True) as mock_ff:
                mock_ff.return_value = ['fixed', 'filters']
                res = self.cls._process(policy)
        assert res == {
            'foo': 'bar',
            'baz': 'blam',
        }
        assert mock_fa.mock_calls == []
        assert mock_ff.mock_calls == []


class TestFixFilters(NotifyOnlyTester):

    def test_simple(self):
        self.cls._mark_for_op_tags = ['tagA', 'tagB']
        filters = [
            {'tag:tagA': 'absent'},
            {'State.Name': 'running'},
            {'tag:something': 'present'},
            {'or': [
                {'and': [
                    {'something': 'else'},
                    {'tag:tagA': 'present'}
                ]},
                {'tag:tagB': 'absent'},
                {'something': 'different'},
                'not-a-dict'
            ]}
        ]
        expected = [
            {'tag:tagA-notify-only': 'absent'},
            {'State.Name': 'running'},
            {'tag:something': 'present'},
            {'or': [
                {'and': [
                    {'something': 'else'},
                    {'tag:tagA-notify-only': 'present'}
                ]},
                {'tag:tagB-notify-only': 'absent'},
                {'something': 'different'},
                'not-a-dict'
            ]}
        ]
        assert self.cls._fix_filters(filters) == expected


class TestFixComment(NotifyOnlyTester):

    def test_simple(self):
        assert self.cls._fix_comment('foo') == 'NOTIFY ONLY: foo'


class TestFixTags(NotifyOnlyTester):

    def test_simple(self):
        assert self.cls._fix_tags(['foo']) == ['foo', 'notify-only']


class TestFixActions(NotifyOnlyTester):

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
            autospec=True
        ) as mocks:
            mocks['_fix_tag_action'].return_value = {'fixed': 'tag'}
            mocks['_fix_mark_for_op_action'].return_value = {'fixed': 'op'}
            mocks['_fix_untag_action'].return_value = {'fixed': 'untag'}
            res = self.cls._fix_actions(actions)
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
            call(self.cls, {'type': 'mark'}),
            call(self.cls, {'type': 'tag'})
        ]
        assert mocks['_fix_mark_for_op_action'].mock_calls == [
            call(self.cls, {'type': 'mark-for-op'})
        ]
        assert mocks['_fix_untag_action'].mock_calls == [
            call(self.cls, {'type': 'remove-tag'}),
            call(self.cls, {'type': 'unmark'}),
            call(self.cls, {'type': 'untag'}),
        ]


class TestFixNotifyAction(NotifyOnlyTester):

    def test_no_description(self):
        policy = {
            'type': 'notify',
            'subject': 'foo'
        }
        assert self.cls._fix_notify_action(policy) == policy

    def test_description(self):
        policy = {
            'type': 'notify',
            'subject': 'foo',
            'violation_desc': 'Violation',
            'action_desc': 'actionDesc'
        }
        assert self.cls._fix_notify_action(policy) == {
            'type': 'notify',
            'subject': 'foo',
            'violation_desc': 'NOTIFY ONLY: Violation',
            'action_desc': 'in the future (currently notify-only) actionDesc'
        }


class TestFixTagAction(NotifyOnlyTester):

    def test_tag(self):
        policy = {
            'action': 'mark',
            'tag': 'foo',
            'value': 'bar'
        }
        assert self.cls._fix_tag_action(policy) == {
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
        assert self.cls._fix_tag_action(policy) == {
            'action': 'mark',
            'key': 'foo-notify-only',
            'value': 'bar'
        }

    def test_tags(self):
        policy = {
            'action': 'mark',
            'tags': {'foo': 'bar', 'baz': 'blam'}
        }
        assert self.cls._fix_tag_action(policy) == {
            'action': 'mark',
            'tags': {'foo-notify-only': 'bar', 'baz-notify-only': 'blam'}
        }

    def test_default_tag(self):
        policy = {
            'action': 'mark',
            'value': 'bar'
        }
        assert self.cls._fix_tag_action(policy) == {
            'action': 'mark',
            'tag': f'{DEFAULT_TAG}-notify-only',
            'value': 'bar'
        }


class TestFixMarkForOpAction(NotifyOnlyTester):

    def test_tag_present(self):
        policy = {
            'action': 'mark-for-op',
            'op': 'foo',
            'tag': 'mytag',
            'days': 7
        }
        assert self.cls._mark_for_op_tags == []
        assert self.cls._fix_mark_for_op_action(policy) == {
            'action': 'mark-for-op',
            'op': 'foo',
            'tag': 'mytag-notify-only',
            'days': 7
        }
        assert self.cls._mark_for_op_tags == ['mytag']

    def test_tag_not_present(self):
        policy = {
            'action': 'mark-for-op',
            'op': 'foo',
            'days': 7
        }
        self.cls._mark_for_op_tags = ['foo', 'bar']
        assert self.cls._fix_mark_for_op_action(policy) == {
            'action': 'mark-for-op',
            'op': 'foo',
            'tag': f'{DEFAULT_TAG}-notify-only',
            'days': 7
        }
        assert self.cls._mark_for_op_tags == ['foo', 'bar', DEFAULT_TAG]


class TestFixUntagAction(NotifyOnlyTester):

    def test_simple(self):
        assert self.cls._fix_untag_action({
            'tags': ['foo', 'bar'],
            'baz': 'blam',
            'action': 'untag'
        }) == {
            'tags': ['foo-notify-only', 'bar-notify-only'],
            'baz': 'blam',
            'action': 'untag'
        }

    def test_tags_not_present(self):
        assert self.cls._fix_untag_action({
            'baz': 'blam',
            'action': 'untag'
        }) == {
            'tags': [f'{DEFAULT_TAG}-notify-only'],
            'baz': 'blam',
            'action': 'untag'
        }
