import json
import logging
import requests
import traceback
import validators

from flask import Flask, request, render_template, jsonify, make_response


AIOGRAM_PORT = 3001
AIOGRAM_URL = f'http://localhost:{AIOGRAM_PORT}'

application = Flask(__name__)


@application.errorhandler(Exception)
def not_found(error):
    return render_template('not_found.html', error_code=error.code)


@application.route('/webhook')
def webhook():
    if request.content_type == 'application/json':
        try:
            data = request.json
            requests.post(AIOGRAM_URL, data=json.dumps(data), headers=request.headers, timeout=10)
        except Exception:
            logging.warning(traceback.format_exc())
    return jsonify({'status': 'Ok'})


@application.route('/')
def index():
    q = request.args.get('q')
    if not q or not validators.url(q):
        return render_template('hello.html')
    return render_template('index.html', q=q)


if __name__ == '__main__':
    application.run(host='0.0.0.0')
