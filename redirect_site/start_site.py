from flask import Flask, request, render_template, abort
import validators


application = Flask(__name__)


@application.route('/')
def index():
    q = request.args.get('q')
    if not q or not validators.url(q):
        abort(404)
    return render_template('index.html', q=q)


if __name__ == '__main__':
    application.run(host='0.0.0.0')
