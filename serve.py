#!/usr/bin/env python

import subprocess

from bottle import route, run, template

subprocess.call(['python3', 'keep-wifi-up.py'])

@route('/hello/<name>')
def index(name):
    return template('<b>Hello {{name}}</b>!', name=name)

run(host='localhost', port=8080)
