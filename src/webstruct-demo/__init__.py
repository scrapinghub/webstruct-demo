from flask import Flask, render_template, request
import joblib
from lxml.html import html5parser
import lxml.html
import requests
import yarl


webstruct_demo = Flask(__name__, instance_relative_config=True)
webstruct_demo.config.from_pyfile('config.py')


def absolutize_link(link, base_url):
    try:
        target_url = yarl.URL(link)
    except:
        return link

    if target_url.is_absolute() and target_url.scheme:
        return link

    if target_url.is_absolute() and not target_url.scheme:
        target_url = target_url.with_scheme(base_url.scheme)
        return str(target_url)

    try:
        target_url = base_url.join(target_url)
    except:
        return link

    return str(target_url)


def absolute_links(tree, url):
    _LINK_SOURCES = ['src', 'href']

    try:
        base_url = yarl.URL(url)
    except:
        return tree

    for _, element in lxml.html.etree.iterwalk(tree, events=('start', )):
        if not isinstance(element.tag, str):
            continue

        for attr in _LINK_SOURCES:
            if attr not in element.attrib:
                continue

            element.attrib[attr] = absolutize_link(element.attrib[attr], base_url)

    return tree


def parent_links(tree, output):
    for _, element in lxml.html.etree.iterwalk(tree, events=('start', )):
        if not isinstance(element.tag, str):
            continue

        if element.tag != 'a':
            continue

        if 'href' not in element.attrib:
            continue

        url = element.attrib['href']

        element.attrib['target'] = '_parent'
        element.attrib['href'] = str(yarl.URL.build(
            path='/',
            query={'url':url, 'output': output})
            )

    return tree


def remove_namespace(tree):
    _NS="{http://www.w3.org/1999/xhtml}"
    for _, element in lxml.html.etree.iterwalk(tree, events=('start', )):
        if not isinstance(element.tag, str):
            continue
        if not element.tag.startswith(_NS):
            continue
        element.tag = element.tag[len(_NS):]

    return tree


@webstruct_demo.route('/')
def index():
    url = request.args.get('url', 'http://en.wikipedia.org/')
    output = request.args.get('output', 'html')

    response = requests.get(url)

    tree = html5parser.document_fromstring(response.content.decode(response.encoding))
    tree = remove_namespace(tree)
    tree = absolute_links(tree, url)
    tree = parent_links(tree, output)
    content = lxml.html.tostring(tree).decode(response.encoding)

    model = joblib.load(webstruct_demo.config['MODEL_PATH'])

    values = {'url': url, 'output': output, 'iframe': content}
    return render_template('main.html', **values)
