from flask import Flask, render_template
from flask_sockets import Sockets

from SpeechClientBridge import SpeechClientBridge
from google.cloud.speech_v1 import enums
from google.cloud.speech_v1 import types

import json
import base64
import os
import time

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/Max/Python/Fraud Calls/My First Project-4e376941f80f.json"
HTTP_SERVER_PORT = 5000

config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.MULAW,
    sample_rate_hertz=8000,
    language_code='en-US')
streaming_config = types.StreamingRecognitionConfig(
    config=config,
    interim_results=True)

app = Flask(__name__)
sockets = Sockets(app)

@app.route('/home')
def home():
    return render_template("index.html")

@app.route('/twiml', methods=['POST'])
def return_twiml():
    print("POST TwiML")
    return render_template('streams.xml')

def on_transcription_response(response):
    if not response.results:
        return

    result = response.results[0]
    if not result.alternatives:
        return

    transcription = result.alternatives[0].transcript
    print("Transcription: " + transcription)

@sockets.route('/')
def transcript(ws):
    print("WS connection opened")
    start =time.time()
    bridge = SpeechClientBridge(
        streaming_config, 
        on_transcription_response
    )
    end = time.time()
    print(end-start)
    
    while not ws.closed:
        message = ws.receive()
        if message is None:
            bridge.terminate()
            break

        data = json.loads(message)
        if data["event"] in ("connected", "start"):
            print(f"Media WS: Received event '{data['event']}': {message}")
            continue
        if data["event"] == "media":
            media = data["media"]
            chunk = base64.b64decode(media["payload"])
            bridge.add_request(chunk)
        if data["event"] == "stop":
            print(f"Media WS: Received event 'stop': {message}")
            print("Stopping...")
            break

    bridge.terminate()
    print("WS connection closed")

if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler)
    print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
    server.serve_forever()

