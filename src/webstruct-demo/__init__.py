import functools
import logging
import random

from flask import Flask, render_template, request
import joblib
from lxml.html import html5parser
import lxml.html
import requests
import yarl

import webstruct.model
import webstruct.sequence_encoding
import webstruct.webannotator


webstruct_demo = Flask(__name__, instance_relative_config=True)
webstruct_demo.config.from_pyfile('config.py')


def absolutize_link(link, base_url):
    if link.startswith('#'):
        return link

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

        if url.startswith('#'):
            continue

        element.attrib['target'] = '_parent'
        element.attrib['href'] = str(base_url.update_query(url=url))

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


def download(url):
    splash_url = webstruct_demo.config.get('SPLASH_URL', None)
    splash_user = webstruct_demo.config.get('SPLASH_USER', None)
    splash_pass = webstruct_demo.config.get('SPLASH_PASS', None)

    is_splash = functools.reduce(lambda x,y: x and y is not None,
                                 [splash_url, splash_user, splash_pass],
                                 True)

    if not is_splash:
        response = requests.get(url)
        return response.content, response.url

    load = {'url': url,
            'images': 0,
            'base_url': url}
    response = requests.post(splash_url + '/render.html',
                             json=load,
                             auth=requests.auth.HTTPBasicAuth(splash_user, splash_pass))

    return response.content, url


def extract_ner(response_content, response_url, base_url):
    url = response_url
    tree = html5parser.document_fromstring(response_content)
    tree = remove_namespace(tree)
    tree = absolute_links(tree, url)
    tree = parent_links(tree, base_url)

    title = tree.xpath('//title')[0].text

    model = joblib.load(webstruct_demo.config['MODEL_PATH'])
    tree, tokens, tags = run_model(tree, model)
    tree = model.html_tokenizer.detokenize_single(tokens, tags)
    tree = webstruct.webannotator.to_webannotator(
            tree,
            entity_colors=model.entity_colors,
            url=url
            )
    content = lxml.html.tostring(tree, encoding='utf-8').decode('utf-8')
    entities = webstruct.sequence_encoding.IobEncoder.group(zip(tokens, tags))
    entities = webstruct.model._drop_empty(
        (model.build_entity(tokens), tag)
        for (tokens, tag) in entities if tag != 'O'
    )
    groups = webstruct.model.extract_entitiy_groups(
            tokens,
            tags,
            dont_penalize=None,
            join_tokens=model.build_entity
            )

    return content, title, entities, groups


def sample_entities(entities):
    unique = list(set(entities))
    random.shuffle(unique)
    sampled = unique[:5]
    sampled = sorted(sampled, key=lambda e:(e[1], e[0]))
    return sampled


def sample_groups(groups):
    groups = [tuple(sorted(g)) for g in groups]
    sampled = sorted(list(set(groups)), key=lambda g:-len(g))
    return sampled[:2]


@webstruct_demo.route('/')
def index():
    url = request.args.get('url', 'http://en.wikipedia.org/')
    output = request.args.get('output', 'html')

    try:
        response_content, response_url = download(url)
        content, title, entities, groups = extract_ner(response_content,
                                                       response_url,
                                                       request.url)
    except:
        logging.exception('Got exception')
        content = None
        title = 'Error during obtaining %s' % (url, )
        entities = []
        groups = []

    _TEMPLATE_MAPPING = {'html': 'main.html',
                         'entities': 'entities.html',
                         'groups': 'groups.html'}

    template = _TEMPLATE_MAPPING.get(output, _TEMPLATE_MAPPING['html'])

    sampled_entities = sample_entities(entities)
    sampled_groups = sample_groups(groups)

    base_url = yarl.URL(request.url)
    routing = {t: str(base_url.update_query(output=t)) for t in ['html', 'entities', 'groups']}

    values = {'url': url,
              'title': title,
              'entities': entities,
              'sampled_entities': sampled_entities,
              'sampled_groups': sampled_groups,
              'routing': routing,
              'srcdoc': content,
              'groups': groups,
              'output': output}

    return render_template(template, **values)
