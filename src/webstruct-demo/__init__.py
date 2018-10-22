from flask import Flask, render_template, request

webstruct_demo = Flask(__name__, instance_relative_config=True)
webstruct_demo.config.from_object('config')

@webstruct_demo.route('/')
def index():
    url = request.args.get('url', 'http://en.wikipedia.org/')
    output = request.args.get('output', 'html')
    values = { 'url': url, 'output': output }
    return render_template('main.html', **values)
