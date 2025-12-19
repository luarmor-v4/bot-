from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return '''
    <html>
        <head><title>Key Bot</title></head>
        <body style="background:#1a1a2e;color:white;text-align:center;padding-top:100px;">
            <h1>🤖 Bot is Running!</h1>
            <p>Discord Key System Bot</p>
        </body>
    </html>
    '''

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
