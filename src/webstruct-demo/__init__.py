from flask import Flask, render_template, request
import joblib
from lxml.html import html5parser, document_fromstring
import lxml.html
import requests
import yarl

import webstruct.model
import webstruct.sequence_encoding
import webstruct.webannotator


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


def parent_links(tree, base_url):
    base_url = yarl.URL(base_url)
    for _, element in lxml.html.etree.iterwalk(tree, events=('start', )):
        if not isinstance(element.tag, str):
            continue

        if element.tag != 'a':
            continue

        if 'href' not in element.attrib:
            continue

        url = element.attrib['href']

        element.attrib['target'] = '_parent'
        element.attrib['href'] = str(base_url.with_query(url=url))

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


_TOKENS_PER_PART = 2000
def run_model(tree, model):
    html_tokens, _ = model.html_tokenizer.tokenize_single(tree)
    if not html_tokens:
        return tree, list(), list()
    tree = html_tokens[0].elem.getroottree().getroot()
    tags = model.model.predict([html_tokens[i:i+_TOKENS_PER_PART] for i in range(0, len(html_tokens), _TOKENS_PER_PART)])
    tags = [i for t in tags for i in t]
    return tree, html_tokens, tags


def get_html_content(response, base_url, output):
    url = response.url
    tree = html5parser.document_fromstring(response.content)
    tree = remove_namespace(tree)
    tree = absolute_links(tree, url)
    tree = parent_links(tree, base_url)

    title = tree.xpath('//title')[0].text

    model = joblib.load(webstruct_demo.config['MODEL_PATH'])
    tree, tokens, tags = run_model(tree, model)
    if output == 'html':
        tree = model.html_tokenizer.detokenize_single(tokens, tags)
        tree = webstruct.webannotator.to_webannotator(
                tree,
                entity_colors=model.entity_colors,
                url=url
                )
        content = lxml.html.tostring(tree).decode(response.encoding)
    elif output == 'entities':
        entities = webstruct.sequence_encoding.IobEncoder.group(zip(tokens, tags))
        entities = webstruct.model._drop_empty(
            (model.build_entity(tokens), tag)
            for (tokens, tag) in entities if tag != 'O'
        )
        content = webstruct_demo.jinja_env.get_template('entities.html').render(entities=entities)
    else:
        groups = webstruct.model.extract_entitiy_groups(
                tokens,
                tags,
                dont_penalize=None,
                join_tokens=model.build_entity
                )
        content = webstruct_demo.jinja_env.get_template('groups.html').render(groups=groups)

    return content, title



@webstruct_demo.route('/')
def index():
    url = request.args.get('url', 'http://en.wikipedia.org/')
    output = request.args.get('output', 'html')

    try:
        response = requests.get(url)
        content, title = get_html_content(response, request.url, output)
        iframe_url = None
    except:
        content = None
        title = ''
        iframe_url = url

    values = {'url': url,
              'output': output,
              'srcdoc': content,
              'srcurl': iframe_url,
              'title': title}

    return render_template('main.html', **values)
