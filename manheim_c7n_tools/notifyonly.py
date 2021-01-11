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
from c7n.tags import DEFAULT_TAG

logger = logging.getLogger(__name__)


class NotifyOnlyPolicy:
    """
    This class converts a c7n policy to a "notify only" policy. See
    :ref:`policies.notify_only` for details.

    IMPORTANT: When making changes to this class, be SURE to update
    :ref:`policies.notify_only` in the documentation.
    """

    @staticmethod
    def as_notify_only(policy: dict) -> dict:
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
                policy[k] = NotifyOnlyPolicy._fix_comment(policy[k])
            if k == 'tags':
                policy[k] = NotifyOnlyPolicy._fix_tags(policy[k])
            if k == 'actions':
                policy[k] = NotifyOnlyPolicy._fix_actions(policy[k])
        return policy

    @staticmethod
    def _fix_comment(comment: str) -> str:
        """
        Convert a policy comment/comments/description to a notify only version,
        by prefixing it with the string "NOTIFY ONLY: ".

        :param comment: the original policy comment
        :type comment: str
        :return: the modified comment
        :rtype: str
        """
        return f'NOTIFY ONLY: {comment}'

    @staticmethod
    def _fix_tags(tags: List[str]) -> List[str]:
        """
        Convert a policy tags list to a notify only version, by appending a
        ``notify-only`` tag to the list.

        :param tags: the original tags list
        :type tags: list
        :return: the modified list, with a notify-only tag appended
        :rtype: list
        """
        return tags + ['notify-only']

    @staticmethod
    def _fix_actions(original: List) -> List:
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
                result.append(NotifyOnlyPolicy._fix_notify_action(item))
            if a_type == 'mark' or a_type == 'tag':
                result.append(NotifyOnlyPolicy._fix_tag_action(item))
            elif a_type == 'mark-for-op':
                result.append(NotifyOnlyPolicy._fix_mark_for_op_action(item))
            elif a_type in ['remove-tag', 'unmark', 'untag']:
                result.append(NotifyOnlyPolicy._fix_untag_action(item))
            else:
                logger.info(
                    'NotifyOnlyPolicy - removing %s action: %s', a_type, item
                )
                continue
        return result

    @staticmethod
    def _fix_notify_action(item: dict) -> dict:
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

    @staticmethod
    def _fix_tag_action(item: dict) -> dict:
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

    @staticmethod
    def _fix_mark_for_op_action(item: dict) -> dict:
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
        item['tag'] += '-notify-only'
        return item

    @staticmethod
    def _fix_untag_action(item: dict) -> dict:
        """
        Fix a ``remove-tag`` / ``unmark`` / ``untag`` action for notify-only
        operation.

        All tag names in the ``tags`` list will have ``-notify-only`` appended.

        :param item: the original action
        :type item: dict
        :return: the modified action
        :rtype: dict
        """
        item['tags'] = [f'{tag}-notify-only' for tag in item['tags']]
        return item
