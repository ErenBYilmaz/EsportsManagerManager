import datetime
import json
import os
import re
import sys
import time
from json import JSONDecodeError
from typing import Dict, Any, Union, Optional

import bottle
# noinspection PyUnresolvedReferences
from bottle.ext.websocket import GeventWebSocketServer
# noinspection PyUnresolvedReferences
from bottle.ext.websocket import websocket
from gevent.threading import Lock
from geventwebsocket import WebSocketError
from geventwebsocket.websocket import WebSocket

from data import server_gamestate
from data.app_game_state import AppGameState
from network import connection
from debug import debug

from lib.print_exc_plus import print_exc_plus
from lib.threading_timer_decorator import exit_after
from lib.util import rename
from network.routes import valid_post_routes

FRONTEND_RELATIVE_PATH = './html'

request_lock = Lock()

if debug:
    TIMEOUT = 600
else:
    TIMEOUT = 5


def reset_global_variables():
    del connection.push_message_queue[:]
    bottle.response.status = 500


@exit_after(TIMEOUT)
def call_controller_method_with_timeout(method, json_request: Dict[str, Any]):
    return method(json_request)


def _process(path, json_request):
    start = time.perf_counter()
    path = path.strip().lower()
    bottle.response.content_type = 'application/json; charset=latin-1'
    reset_global_variables()
    # noinspection PyBroadException
    try:
        json_request = json_request()
        if json_request is None:
            bottle.response.status = 400
            resp = connection.bad_request('Only json allowed.')
        elif path not in valid_post_routes:
            print('Processing time:', time.perf_counter() - start)
            resp = connection.not_found('URL not available')
        else:
            method_to_call = valid_post_routes[path](None).from_client
            resp = call_controller_method_with_timeout(method_to_call, json_request)
        if not isinstance(resp, dict):
            raise AssertionError('The response should always be a dict')
        if 'error' in resp:
            bottle.response.status = int(resp['error'][:3])
        else:
            bottle.response.status = 200
        if bottle.response.status_code == 200:
            server_gamestate.gs.commit()
            connection.push_messages_in_queue()
        else:
            server_gamestate.gs.rollback()
        print('route=' + path, f't={time.perf_counter() - start:.4f}s,')
        return resp
    except JSONDecodeError:
        return handle_error('Unable to decode JSON', path, start)
    except NotImplementedError:
        return handle_error('This feature has not been fully implemented yet.', path, start)
    except KeyboardInterrupt:
        if time.perf_counter() - start > TIMEOUT:
            return handle_error('Processing timeout', path, start)
        else:
            raise
    except Exception:
        return handle_error('Unknown error', path, start)


def server_call(game_name: str, port: Optional[Union[int, str]] = None):
    args = [game_name]
    if port is not None:
        args.append(str(port))
    if os.path.isfile('run_server.py'):
        return ['python', '-m', 'run_server', *args]
    elif os.path.isfile('run_server.exe'):
        return ['run_server.exe', *args]


if __name__ == '__main__':
    if debug:
        print('Running server in debug mode...')

    if len(sys.argv) <= 1:
        raise RuntimeError(f'Missing required parameter: game name\n Example call ´{" ".join(server_call("mygamename123"))}´')
    if AppGameState.save_file_exists(sys.argv[1]):
        server_gamestate.gs = AppGameState.load(sys.argv[1])
    else:
        server_gamestate.gs = AppGameState(users=[], game_name=sys.argv[1])
    if len(sys.argv) >= 3:
        connection.PORT = int(sys.argv[2])


    @bottle.route('/json/<path>', method='POST')
    def process(path):
        with request_lock:
            return _process(path, lambda: bottle.request.json)


    @bottle.route('/', method='GET')
    def index():
        if connection.ROOT_URL != '/':
            bottle.redirect(connection.ROOT_URL)


    def handle_error(message, path, start):
        bottle.response.status = 500
        print_exc_plus()
        server_gamestate.gs.rollback()
        print('route=' + str(path), f't={time.perf_counter() - start:.4f}s,')
        return connection.internal_server_error(message)


    @bottle.get('/websocket', apply=[websocket])
    def websocket(ws: WebSocket):
        print('websocket connection', *ws.handler.client_address, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        while True:
            start = time.perf_counter()
            path = None
            request_token = None

            # noinspection PyBroadException
            try:
                if ws.closed:
                    connection.ws_cleanup(ws)
                    break
                try:
                    msg = ws.read_message()
                except ConnectionResetError:
                    msg = None
                except WebSocketError as e:
                    if e.args[0] == 'Unexpected EOF while decoding header':
                        msg = None
                    else:
                        raise

                if msg is not None:  # received some message
                    with request_lock:
                        msg = bytes(msg)

                        outer_json = bottle.json_loads(msg)
                        path = outer_json['route']
                        inner_json = outer_json['body']
                        request_token = outer_json['request_token']
                        inner_result_json = _process(path, lambda: inner_json)

                        if 'error' in inner_result_json:
                            status_code = int(inner_result_json['error'][:3])
                        else:
                            status_code = 200

                        # if there is a session_id involved, associate it with this websocket
                        for json_container in [inner_json, inner_result_json]:
                            if 'session_id' in json_container and server_gamestate.gs.valid_session_id(
                                    json_container['session_id']):
                                user_id = server_gamestate.gs.username_by_session_id(json_container['session_id'])

                                if user_id in connection.websockets_for_user:
                                    if ws not in connection.websockets_for_user[user_id]:
                                        connection.websockets_for_user[user_id].append(ws)
                                else:
                                    connection.websockets_for_user[user_id] = [ws]
                                if ws in connection.users_for_websocket:
                                    if user_id not in connection.users_for_websocket[ws]:
                                        connection.users_for_websocket[ws].append(user_id)
                                else:
                                    connection.users_for_websocket[ws] = [user_id]
                        outer_result_json = {
                            'body': inner_result_json,
                            'http_status_code': status_code,
                            'request_token': request_token
                        }
                        outer_result_json = json.dumps(outer_result_json)
                        if ws.closed:
                            connection.ws_cleanup(ws)
                            break
                        ws.send(outer_result_json)
                        print('websocket message',
                              *ws.handler.client_address,
                              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              status_code,
                              len(outer_result_json))
                else:
                    connection.ws_cleanup(ws)
                    break
            except JSONDecodeError:
                inner_result_json = handle_error('Unable to decode outer JSON', path, start)
                status_code = 500
                inner_result_json['http_status_code'] = status_code
                if request_token is not None:
                    inner_result_json['request_token'] = request_token
                inner_result_json = json.dumps(inner_result_json)
                if ws.closed:
                    connection.ws_cleanup(ws)
                    break
                ws.send(inner_result_json)
                print('websocket message',
                      *ws.handler.client_address,
                      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                      status_code,
                      len(inner_result_json))
            except Exception:
                inner_result_json = handle_error('Unknown error', path, start)
                status_code = 500
                inner_result_json['http_status_code'] = status_code
                if request_token is not None:
                    inner_result_json['request_token'] = request_token
                inner_result_json = json.dumps(inner_result_json)
                if ws.closed:
                    connection.ws_cleanup(ws)
                    break
                ws.send(inner_result_json)
                print('websocket message',
                      *ws.handler.client_address,
                      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                      status_code,
                      len(inner_result_json))


    def _serve_static_directory(route, root, download=False):
        method_name = ''.join(c for c in root if re.match(r'[A-Za-z]]', c))
        assert method_name not in globals()

        @bottle.route(route, method=['GET', 'OPTIONS'])
        @rename(''.join(c for c in root if re.match(r'[A-Za-z]]', c)))
        def serve_static_file(filename):
            if filename == 'api.json':
                return {'endpoint': bottle.request.urlparts[0] + '://' + bottle.request.urlparts[1] + '/json/'}
            if download:
                default_name = 'yse-' + filename
                return bottle.static_file(filename, root=root, download=default_name)
            else:
                return bottle.static_file(filename, root=root, download=False)


    # frontend
    for subdir, dirs, files in os.walk(FRONTEND_RELATIVE_PATH):
        # subdir now has the form   ../frontend/config
        _serve_static_directory(
            route=subdir.replace('\\', '/').replace(FRONTEND_RELATIVE_PATH, '') + '/<filename>',
            root=subdir
        )

    # app
    _serve_static_directory(
        route='/app/<filename>',
        root='../android/app/release',
        download=True,
    )

    bottle.run(host='0.0.0.0', port=connection.PORT, debug=debug, server=GeventWebSocketServer)
    server_gamestate.gs = None
