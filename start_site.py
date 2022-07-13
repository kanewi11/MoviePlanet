from flask import Flask, request, render_template


application = Flask(__name__)


@application.route('/')
def main():
    q = request.args.get('q')
    if not q:
        return render_template('404.html'), 404
    return render_template('main.html', q=q)


if __name__ == '__main__':
    application.run(host='0.0.0.0')
