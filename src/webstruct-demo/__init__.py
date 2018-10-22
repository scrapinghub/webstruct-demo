from flask import Flask, render_template, request
import lxml.html
import requests


webstruct_demo = Flask(__name__, instance_relative_config=True)
webstruct_demo.config.from_object('config')


def fix_hrefs(tree):
    pass


@webstruct_demo.route('/')
def index():
    url = request.args.get('url', 'http://en.wikipedia.org/')
    output = request.args.get('output', 'html')
    response = requests.get(url)

    parser = lxml.html.HTMLParser(encoding=response.encoding)
    tree = lxml.html.document_fromstring(response.content, parser=parser)
    content = lxml.html.etree.tostring(tree)

    values = {'url': url, 'output': output, 'iframe': content}
    return render_template('main.html', **values)
