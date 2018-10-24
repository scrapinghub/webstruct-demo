# webstruct-demo
HTTP demo for https://github.com/scrapinghub/webstruct

# How to run locally

Add string to `src/instance/config.py`

```
MODEL_PATH='<path to model file>'
```

For javascript-rendering add [splash](https://splash.readthedocs.io/en/stable/index.html) credentials

```
SPLASH_URL = '<splash_url>'
SPLASH_USER = '<splash_user>'
SPLASH_PASS = '<splash_pass>'
```

And run in command line

```
FLASK_ENV=development FLASK_APP=src/webstruct-demo/__init__.py runinenv.sh ~/ves/webstruct-demo/ flask run --host=0.0.0.0
```

# How to build docker container

1. Put your model file to `build/model.joblib`
2. Add splash credentials to `build/splash_credentials` or leave it empty
3. run container build

```
sudo docker build .
```

4. run container temporarily

```
sudo docker run -ti --rm -p <desired_port>:80 <image_id>
```

4. or run container persistently

```
sudo docker run -p <desired_port>:80 --name webstruct-demo -d --restart=always <image_id>
```
