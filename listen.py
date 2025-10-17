import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer

# --- constants

MODEL_PATH  = "model/vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
BLOCK_SIZE  = 8000
DATA_TYPE   = 'int16'
CHANNELS    = 1

# --- A simple listener class

class Listener:

    # --- constructor

    def __init__(self, callback):
        self.model      = Model(MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, SAMPLE_RATE)
        self.q          = queue.Queue()
        self.callback   = callback
        self.stream     = None
        self.running    = False

    # --- internal audio callback

    def _callback(self, indata, frames, time, status):
        self.q.put(bytes(indata))

    # --- start listening

    def start(self):
        if self.running:
            return

        self.stream = sd.RawInputStream(
            samplerate = SAMPLE_RATE,
            blocksize  = BLOCK_SIZE,
            dtype      = DATA_TYPE,
            channels   = CHANNELS,
            callback   = self._callback
        )

        self.stream.start()
        self.running = True
        print("Listening...")

        try:
            while self.running:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    heard     = json.loads(self.recognizer.Result())
                    utterance = heard.get("text", "").strip()
                    if utterance:
                        self.callback(utterance)

        except KeyboardInterrupt:
            print("Listening Closing...")
            self.stop()

        except Exception as err:
            print(f"Listening Error: { err }")
            self.stop()

    # --- stop listening

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.running = False
        print("Listening Stopped")
