from flask import Flask, render_template

webstruct_demo = Flask(__name__, instance_relative_config=True)
webstruct_demo.config.from_object('config')

@webstruct_demo.route('/')
def index():
    return render_template('main.html')
