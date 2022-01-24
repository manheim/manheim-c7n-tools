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

from typing import List
import logging
import c7n.filters  # noqa - used to fix a circular import error
from c7n.tags import DEFAULT_TAG

logger = logging.getLogger(__name__)


class NotifyOnlyPolicy:
    """
    This class converts a c7n policy to a "notify only" policy. See
    :ref:`policies.notify_only` for details.

    IMPORTANT: When making changes to this class, be SURE to update
    :ref:`policies.notify_only` in the documentation.
    """

    def __init__(self, policy: dict):
        """
        Initialize a NotifyOnlyPolicy.

        :param policy: the original policy
        :type policy: dict
        """
        self._original: dict = policy
        self._mark_for_op_tags: List[str] = []
        self._fixed: dict = self._process(self._original)

    def as_notify_only(self) -> dict:
        """
        Return the policy, converted to a notify-only version.

        :return: converted policy
        :rtype: dict
        """
        return self._fixed

    def _process(self, policy: dict) -> dict:
        """
        Return the given policy, converted to notify-only.

        :param policy: the original c7n policy
        :type policy: dict
        :return: policy, modified for notify-only mode
        :rtype: dict
        """
        if 'notify_only' in policy:
            del policy['notify_only']
        for k in policy.keys():
            if k in ['comment', 'comments', 'description']:
                policy[k] = self._fix_comment(policy[k])
            if k == 'tags':
                policy[k] = self._fix_tags(policy[k])
            if k == 'actions':
                policy[k] = self._fix_actions(policy[k])
        # this needs to happen AFTER all _fix_actions calls...
        if 'filters' in policy:
            policy['filters'] = self._fix_filters(policy['filters'])
        return policy

    def _fix_filters(self, filters: List) -> List:
        """
        Given a list of filters from a policy, update them for any tagging
        changes.

        :param filters: filters from policy, or a subset thereof
        :type filters: list
        :return: fixed filters
        :rtype: list
        """
        tag_changes = {
            f'tag:{x}': f'tag:{x}-notify-only' for x in self._mark_for_op_tags
        }
        for idx, item in enumerate(filters):
            # each item should be a dict
            if not isinstance(item, type({})):
                continue
            for k in list(item.keys()):
                v = item[k]
                if isinstance(v, type([])):
                    item[k] = self._fix_filters(v)
                if k in tag_changes:
                    del item[k]
                    item[tag_changes[k]] = v
        return filters

    def _fix_comment(self, comment: str) -> str:
        """
        Convert a policy comment/comments/description to a notify only version,
        by prefixing it with the string "NOTIFY ONLY: ".

        :param comment: the original policy comment
        :type comment: str
        :return: the modified comment
        :rtype: str
        """
        return f'NOTIFY ONLY: {comment}'

    def _fix_tags(self, tags: List[str]) -> List[str]:
        """
        Convert a policy tags list to a notify only version, by appending a
        ``notify-only`` tag to the list.

        :param tags: the original tags list
        :type tags: list
        :return: the modified list, with a notify-only tag appended
        :rtype: list
        """
        return tags + ['notify-only']

    def _fix_actions(self, original: List) -> List:
        """
        Given a list of actions from a policy, return a new list of notify-only
        actions.

        * ``notify`` actions will be included unmodified
        * ``mark`` / ``tag`` actions will be passed through
          :py:meth:`~._fix_tag_action` and the result included
        * ``mark-for-op`` actions will be passed through
          :py:meth:`~._fix_mark_for_op_action` and the result included
        * ``remove-tag`` / ``unmark`` / ``untag`` actions will be passed through
          :py:meth:`~._fix_untag_action` and the result included
        * all other actions will be REMOVED

        :param original: original policy actions list
        :type original: list
        :return: new list of actions
        :rtype: list
        """
        result = []
        for item in original:
            if not isinstance(item, type({})):
                logger.info('NotifyOnlyPolicy - removing action: %s', item)
                continue
            a_type = item.get('type', '')
            if a_type == 'notify':
                result.append(self._fix_notify_action(item))
            if a_type == 'mark' or a_type == 'tag':
                result.append(self._fix_tag_action(item))
            elif a_type == 'mark-for-op':
                result.append(self._fix_mark_for_op_action(item))
            elif a_type in ['remove-tag', 'unmark', 'untag']:
                result.append(self._fix_untag_action(item))
            else:
                logger.info(
                    'NotifyOnlyPolicy - removing %s action: %s', a_type, item
                )
                continue
        return result

    def _fix_notify_action(self, item: dict) -> dict:
        """
        Fix a ``notify`` action for notify-only operation.

        If the ``violation_desc`` key is present, its value will be prefixed
        with ``NOTIFY ONLY: ``. If the ``action_desc`` key is present, its value
        will be prefixed with the string
        ``in the future (currently notify-only)``.

        :param item: the original action
        :type item: dict
        :return: the modified action
        :rtype: dict
        """
        if 'violation_desc' in item:
            item['violation_desc'] = 'NOTIFY ONLY: ' + item['violation_desc']
        if 'action_desc' in item:
            item['action_desc'] = 'in the future (currently notify-only) ' + \
                                  item['action_desc']
        return item

    def _fix_tag_action(self, item: dict) -> dict:
        """
        Fix a ``tag`` / ``mark`` action for notify-only operation.

        The string ``-notify-only`` will be appended to the ``tag`` item,
        ``key`` item, and/or every item in the ``tags`` list.

        If none of these values are set, the ``tag`` item will be set to the
        custodian ``DEFAULT_TAG``, suffixed with ``-notify-only``.

        :param item: the original action
        :type item: dict
        :return: the modified action
        :rtype: dict
        """
        if 'tag' in item:
            item['tag'] = item['tag'] + '-notify-only'
        if 'key' in item:
            item['key'] = item['key'] + '-notify-only'
        if 'tags' in item:
            item['tags'] = {
                f'{k}-notify-only': v for k, v in item['tags'].items()
            }
        if 'tag' not in item and 'key' not in item and 'tags' not in item:
            item['tag'] = f'{DEFAULT_TAG}-notify-only'
        return item

    def _fix_mark_for_op_action(self, item: dict) -> dict:
        """
        Fix a ``mark-for-op`` action for notify-only operation.

        The string ``notify-only`` will be appended to the tag name used.

        :param item: the original action
        :type item: dict
        :return: the modified action
        :rtype: dict
        """
        if 'tag' not in item:
            item['tag'] = DEFAULT_TAG
        self._mark_for_op_tags.append(item['tag'])
        item['tag'] += '-notify-only'
        return item

    def _fix_untag_action(self, item: dict) -> dict:
        """
        Fix a ``remove-tag`` / ``unmark`` / ``untag`` action for notify-only
        operation.

        All tag names in the ``tags`` list will have ``-notify-only`` appended.

        :param item: the original action
        :type item: dict
        :return: the modified action
        :rtype: dict
        """
        if 'tags' not in item:
            item['tags'] = [f'{DEFAULT_TAG}']
        item['tags'] = [f'{tag}-notify-only' for tag in item['tags']]
        return item
