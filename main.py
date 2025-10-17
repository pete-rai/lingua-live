import time
import logging
from buffer    import ReviewBuffer
from listen    import Listener
from analyse   import Analyser
from threading import Thread
from flask     import Flask, send_from_directory, jsonify, request

# --- constants

DEPTH_UTTERANCE = 60 * 3 # seconds
DEPTH_ANALYSIS  = 60 * 4 # seconds
FILE_STATICS    = "static"
FILE_CLIENT     = "index.html"
SERVER_PORT     = 8001

# --- globals

server     = Flask(__name__, static_folder = FILE_STATICS)
utterances = ReviewBuffer(max_age = DEPTH_UTTERANCE)
analysis   = ReviewBuffer(max_age = DEPTH_ANALYSIS)
analyser   = Analyser()

# --- configuration

logging.getLogger('werkzeug').disabled = True
server.logger.disabled = True

# --- base route

@server.route("/")
def index():
    return send_from_directory(server.static_folder, FILE_CLIENT)

# --- reset route

@server.route("/reset")
def reset():
    print("Resetting")
    analysis.clear()
    utterances.clear()
    return "", 200

# --- remove route

@server.route("/remove", methods=["POST"])
def remove():
    body = request.get_json()
    name = body["name"]

    print(f"Removing: '{name}'")
    analysis.remove(name)
    return "", 200

# --- context route

@server.route("/context", methods=["POST"])
def context():
    body    = request.get_json()
    context = body["context"]

    print(f"Context: '{context}'")
    analyser.context(context)
    analysis.clear()
    return "", 200

# --- analysis route

@server.route("/analysis")
def items():
    return analysis.items, 200, { "Content-Type": "application/json" }

# --- heard and utterance

def heard(utterance):
    utterances.add(utterance)
    print("-----------------------------------------")
    print("Buffer:", utterances.text)
    print("-----------------------------------------")

    # --- analyse an utterance

    def analyse():
        print("Analysing...")
        started = time.time();
        results = analyser.analyse(utterances.text)
        print(f"Analysis took: {time.time() - started:.1f}s")

        for entry in results:
            analysis.add(entry["text"], meta = entry["type"], name = entry["name"].capitalize())

    Thread(target = analyse, daemon = True).start()

# --- entry point

listener = Listener(callback = heard)
Thread(target = listener.start, daemon = True).start() # start listening

server.run(host = "0.0.0.0", port = SERVER_PORT) # start serving
