import datetime
import json
from typing import Dict, List

import requests
from geventwebsocket import WebSocketError
from geventwebsocket.websocket import WebSocket

from network.my_types import MessageType, Message, UserName, MessageQueue

PORT = 15291
ROOT_URL = "/index.html"

websockets_for_user: Dict[UserName, List[WebSocket]] = {}
users_for_websocket: Dict[WebSocket, List[UserName]] = {}
push_message_queue: MessageQueue = []


def not_found(msg=''):
    msg = '404: ' + msg
    return {"error": msg}


def unavailable_for_legal_reasons(msg=''):
    msg = '451: ' + msg
    return {"error": msg}


def forbidden(msg=''):
    msg = '403: ' + msg
    return {"error": msg}


def unauthorized(msg=''):
    msg = '401: ' + msg
    return {"error": msg}


def bad_request(msg=''):
    msg = '400: ' + msg
    return {"error": msg}


def internal_server_error(msg=''):
    msg = '500: ' + msg
    return {"error": msg}


def locked(msg=''):
    msg = '423: ' + msg
    return {"error": msg}


def precondition_failed(msg=''):
    msg = '412: ' + msg
    return {"error": msg}


def json_request(url, data):
    # print('Sending to ' + url + ': ' + str(json.dumps(data)))
    r = requests.post(url,
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json; charset=latin-1'})
    # print('Request returned: ' + str(r.content))
    return r.json()


def push_message(recipient_ids: List[UserName], contents: Message, message_type: MessageType):
    from network.routes import push_message_types
    if message_type not in push_message_types:
        raise AssertionError('Invalid message type.')
    sockets = {socket for user_id in recipient_ids for socket in websockets_for_user.get(user_id, [])}
    if len(sockets) > 0:
        message = {'message_type': message_type, 'contents': contents}
        for ws in sockets:
            if ws.closed:
                ws_cleanup(ws)
                continue
            message = json.dumps({'message_type': message_type, 'contents': contents})
            ws.send(message)
        print(message_type,
              'to',
              len(sockets),
              'sockets',
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              len(message))


def enqueue_push_message(recipient_ids: List[UserName], contents: Dict, message_type: str):
    from network.routes import push_message_types
    assert message_type in push_message_types
    recipient_ids = [user_id for user_id in recipient_ids]
    if len(recipient_ids) == 0:
        return
    recipient_ids = [user_id for user_id in recipient_ids]
    push_message_queue.append((recipient_ids, contents, message_type))


def ws_cleanup(ws):
    if ws in users_for_websocket:
        users_affected = users_for_websocket[ws]
        for user_id in users_affected:
            # remove the websocket from all lists
            websockets_for_user[user_id][:] = filter(lambda s: s != ws,
                                                     websockets_for_user[user_id])
        del users_for_websocket[ws]
        if not ws.closed:
            ws.close()
    print('websocket connection ended',
          *ws.handler.client_address,
          datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), )


def preprocess_push_message_queue(queue: MessageQueue) -> MessageQueue:
    return queue


def push_messages_in_queue():
    global push_message_queue

    push_message_queue = preprocess_push_message_queue(push_message_queue)

    for message in push_message_queue:
        try:
            push_message(*message)
        except WebSocketError:
            continue
        except ConnectionResetError:
            continue
    del push_message_queue[:]
