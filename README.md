# webstruct-demo
HTTP demo for https://github.com/scrapinghub/webstruct

# How to run locally

Add string to `src/instance/config.py`

```
MODEL_PATH='<path to model file>'
```

And run in command line

```
FLASK_ENV=development FLASK_APP=src/webstruct-demo/__init__.py runinenv.sh ~/ves/webstruct-demo/ flask run --host=0.0.0.0
```
