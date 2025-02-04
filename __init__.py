from flask import Flask
from config import *

app = Flask(__name__)
app.config.from_object('config')
from flask import Flask, request
@app.route("/")
def index():
    ip = request.remote_addr
    return f"Ваш IP-адрес: {ip}"

if __name__ == "__main__":
    app.run()