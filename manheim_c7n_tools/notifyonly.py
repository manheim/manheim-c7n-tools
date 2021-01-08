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
    This class converts a c7n policy to a "notify only" policy. The changes are:

    * Update the comment, comments, and description with a notify-only prefix.
    * If the policy already has ``tags``, add a "notify-only" tag.
    * Remove any actions other than: mark, mark-for-op, notify, remove-tag, tag,
      unmark, untag
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
        return f'NOTIFY ONLY: {comment}'

    @staticmethod
    def _fix_tags(tags: List[str]) -> List[str]:
        return tags + ['notify-only']

    @staticmethod
    def _fix_actions(original: List) -> List:
        result = []
        for item in original:
            if not isinstance(item, type({})):
                logger.info('NotifyOnlyPolicy - removing action: %s', item)
                continue
            a_type = item.get('type', '')
            if a_type == 'notify':
                result.append(item)
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
    def _fix_tag_action(item: dict) -> dict:
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
        if 'tag' not in item:
            item['tag'] = DEFAULT_TAG
        item['tag'] += '-notify-only'
        return item

    @staticmethod
    def _fix_untag_action(item: dict) -> dict:
        item['tags'] = [f'{tag}-notify-only' for tag in item['tags']]
        return item
