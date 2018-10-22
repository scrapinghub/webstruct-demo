from flask import Flask, render_template, request
import lxml.html
import requests
import yarl


webstruct_demo = Flask(__name__, instance_relative_config=True)
webstruct_demo.config.from_object('config')


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

            try:
                target_url = yarl.URL(element.attrib[attr])
            except:
                continue

            if target_url.is_absolute():
                continue

            try:
                target_url = base_url.join(target_url)
            except:
                continue

            element.attrib[attr] = str(target_url)

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


@webstruct_demo.route('/')
def index():
    url = request.args.get('url', 'http://en.wikipedia.org/')
    output = request.args.get('output', 'html')

    response = requests.get(url)

    parser = lxml.html.HTMLParser(encoding=response.encoding)
    tree = lxml.html.document_fromstring(response.content, parser=parser)
    tree = absolute_links(tree, url)
    tree = parent_links(tree, output)
    content = lxml.html.etree.tostring(tree).decode(response.encoding)

    values = {'url': url, 'output': output, 'iframe': content}
    return render_template('main.html', **values)
