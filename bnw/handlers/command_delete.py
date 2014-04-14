# -*- coding: utf-8 -*-
# from twisted.words.xish import domish

from base import *
import bnw.core.bnw_objects as objs
from bnw.core.post import publish


def _(s, user):
    return s


@require_auth
@check_arg(message=MESSAGE_COMMENT_RE)
def cmd_delete(request, message="", last=False):
    """ Удаление

    Удаление поста или коммента.

    redeye: delete --message=123456, d -m ABCDEF/123, d --last, d -l
    simple: D #123456, D #ABDEF/123, D L"""
    message = canonic_message_comment(message).upper()
    if last:
        lastcomment = list(objs.Comment.find_sort({'user': request.user['name']}, [('date', -1)], limit=1))
        lastmessage = list(objs.Message.find_sort({'user': request.user['name']}, [('date', -1)], limit=1))
        if lastcomment:
            if lastmessage:
                message = lastmessage[0]['id'] if lastmessage[0][
                    'date'] > lastcomment[0]['date'] else lastcomment[0]['id']
            else:
                message = lastcomment[0]['id']
        else:
            if lastmessage:
                message = lastmessage[0]['id']
            else:
                return dict(ok=False, desc='Nothing to delete.')
    if not message:
        return dict(ok=False, desc='Usage: delete -m POST[/COMMENT]')
    splitpost = message.split('/')
    message_id = splitpost[0].upper()
    comment_id = message if len(splitpost) > 1 else None
    if comment_id:
        comment = objs.Comment.find_one({'id': comment_id, 'message': message_id})
    post = objs.Message.find_one({'id': message_id})
    if comment_id:
        if not comment:
            return dict(ok=False, desc='No such comment')
        if request.user['name'] not in (comment['user'], post['user'], comment.get('real_user'), post.get('real_user')):
            return dict(ok=False, desc='Not your comment and not your message.')
        objs.Message.mupdate({'id': message_id}, {'$inc': {'replycount': -1}})
        objs.Comment.remove({'id': comment['id'], 'message': comment['message'], 'user': comment['user']})
        publish('del_comment_in_' + message_id, comment_id)
        publish('upd_comments_count', message_id, post['replycount'] - 1)
        publish('upd_comments_count_in_' + message_id,
                message_id, post['replycount'] - 1)
        return dict(ok=True, desc='Comment %s removed.' % (comment_id,))
    else:
        if not post:
            return dict(ok=False, desc='No such message.')
        if request.user['name'] not in (post['user'], post.get('real_user')):
            return dict(ok=False, desc='Not your message.')
        objs.Message.remove({'id': post['id'], 'user': post['user']})
        objs.Comment.remove({'message': post['id']})
        publish('del_message', message_id)
        publish('del_message_on_user_' + post['user'], message_id)
        return dict(ok=True, desc='Message %s removed.' % (message,))
