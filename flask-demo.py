import threading
from flask import Flask, request
import time
import os
from functools import partial

app = Flask(__name__)


class _KillMe(BaseException):
    pass

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/shutdown')
def shutdown():
    raise _KillMe


app.run(host='0.0.0.0', port=8051)
