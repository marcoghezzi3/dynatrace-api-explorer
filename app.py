import os
import time
import logging

from flask import Flask, request, jsonify, session
import requests as req_lib

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.urandom(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

# Suppress Werkzeug access log to avoid accidentally logging request bodies
logging.getLogger('werkzeug').setLevel(logging.WARNING)

BLOCKED_HEADERS = {'host', 'content-length', 'transfer-encoding', 'connection', 'authorization'}
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/connect', methods=['POST'])
def connect():
    data = request.get_json(silent=True) or {}
    token = data.get('token', '').strip()
    base_url = data.get('base_url', '').strip().rstrip('/')

    if not token:
        return jsonify({'error': 'Token mancante'}), 400
    if not base_url:
        return jsonify({'error': 'URL ambiente mancante'}), 400
    if not (base_url.startswith('https://') or base_url.startswith('http://localhost') or base_url.startswith('http://127.0.0.1')):
        return jsonify({'error': "L'URL deve iniziare con https://"}), 400

    headers = {'Authorization': f'Api-Token {token}'}
    try:
        resp = req_lib.get(
            f'{base_url}/api/v2/metrics',
            headers=headers,
            params={'pageSize': '1'},
            timeout=10,
            verify=True,
        )
        if resp.status_code == 401:
            return jsonify({'error': 'Token non valido (401 Unauthorized)'}), 401
        if resp.status_code == 403:
            return jsonify({'error': 'Token senza permessi sufficienti (403 Forbidden)'}), 403
        # 404 is acceptable for older/managed environments that may not have v2 metrics
    except req_lib.exceptions.SSLError:
        return jsonify({'error': 'Errore SSL: verifica il certificato dell\'ambiente'}), 502
    except req_lib.exceptions.ConnectionError:
        return jsonify({'error': 'Impossibile raggiungere l\'ambiente Dynatrace'}), 502
    except req_lib.exceptions.Timeout:
        return jsonify({'error': 'Timeout durante la verifica della connessione'}), 504

    # Store in server-side session only — token never returned to browser
    session['token'] = token
    session['base_url'] = base_url
    return jsonify({'status': 'connected', 'base_url': base_url})


@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    session.clear()
    return jsonify({'status': 'disconnected'})


@app.route('/api/status', methods=['GET'])
def status():
    connected = 'token' in session
    return jsonify({
        'connected': connected,
        'base_url': session.get('base_url') if connected else None,
        # token is NEVER returned
    })


@app.route('/api/proxy', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy():
    if 'token' not in session:
        return jsonify({'error': 'Non connesso. Inserisci URL e token prima di inviare richieste.'}), 401

    api_path = request.args.get('path', '').strip()
    if not api_path:
        return jsonify({'error': 'Parametro "path" mancante (es. /api/v2/problems)'}), 400
    if not api_path.startswith('/'):
        api_path = '/' + api_path

    target_url = session['base_url'] + api_path

    # Forward all query params except our internal 'path' key (multi-value aware)
    query_params = {}
    for k in request.args.keys():
        if k == 'path':
            continue
        vals = request.args.getlist(k)
        query_params[k] = vals if len(vals) > 1 else vals[0]

    # Build outbound headers: strip hop-by-hop and auth, inject our token
    outbound_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in BLOCKED_HEADERS
    }
    outbound_headers['Authorization'] = f'Api-Token {session["token"]}'

    body = request.get_data()

    start = time.monotonic()
    try:
        resp = req_lib.request(
            method=request.method,
            url=target_url,
            headers=outbound_headers,
            params=query_params,
            data=body,
            timeout=30,
            verify=True,
            stream=False,
            allow_redirects=True,
        )
    except req_lib.exceptions.Timeout:
        return jsonify({'error': 'Timeout richiesta verso Dynatrace (30s)'}), 504
    except req_lib.exceptions.SSLError as e:
        return jsonify({'error': f'Errore SSL: {str(e)}'}), 502
    except req_lib.exceptions.ConnectionError as e:
        return jsonify({'error': f'Errore di connessione: {str(e)}'}), 502

    elapsed_ms = round((time.monotonic() - start) * 1000)

    content_type = resp.headers.get('Content-Type', 'application/json')
    response_body = resp.content[:MAX_RESPONSE_SIZE]
    truncated = len(resp.content) > MAX_RESPONSE_SIZE

    flask_resp = app.response_class(
        response=response_body,
        status=resp.status_code,
        content_type=content_type,
    )
    flask_resp.headers['X-Response-Time-Ms'] = str(elapsed_ms)
    flask_resp.headers['X-Dynatrace-Status'] = str(resp.status_code)
    if truncated:
        flask_resp.headers['X-Response-Truncated'] = 'true'
    return flask_resp


if __name__ == '__main__':
    print('Dynatrace API Explorer avviato su http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)
