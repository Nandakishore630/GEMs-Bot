# keep_alive.py
from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "I'm alive!"  # Just a simple response to keep the app alive


def run():
    app.run(host='0.0.0.0', port=5000)


def keep_alive():
    t = Thread(target=run)
    t.start()
