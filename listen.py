import queue
import json
import threading
import time
import numpy as np
import pyaudiowpatch as pyaudio
from vosk import Model, KaldiRecognizer

# --- constants

MODEL_PATH  = "model/vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000  # rate expected by the speech model
BLOCK_SECS  = 0.5    # audio captured per block

# --- A single audio source (microphone or speaker loopback) with its own recognizer

class Source:

    # --- constructor

    def __init__(self, audio, device, model, callback):
        self.audio      = audio
        self.device     = device
        self.name       = device["name"]
        self.rate       = int(device["defaultSampleRate"])
        self.channels   = int(device["maxInputChannels"])
        self.recognizer = KaldiRecognizer(model, SAMPLE_RATE)
        self.callback   = callback
        self.q          = queue.Queue()
        self.stream     = None
        self.running    = False
        self.carry      = np.zeros(0, dtype = np.float32)

    # --- audio callback, called by the audio driver

    def _capture(self, data, frames, time, status):
        self.q.put(data)
        return (None, pyaudio.paContinue)

    # --- converts raw audio to 16khz mono 16 bit

    def _convert(self, data):
        samples = np.frombuffer(data, dtype = np.int16).reshape(-1, self.channels).mean(axis = 1)
        samples = np.concatenate((self.carry, samples))

        if self.rate == SAMPLE_RATE:
            self.carry = np.zeros(0, dtype = np.float32)
        elif self.rate % SAMPLE_RATE == 0: # whole number ratio so average the samples
            step       = self.rate // SAMPLE_RATE
            usable     = len(samples) - len(samples) % step
            self.carry = samples[usable:]
            samples    = samples[:usable].reshape(-1, step).mean(axis = 1)
        else:
            self.carry = np.zeros(0, dtype = np.float32)
            count      = int(len(samples) * SAMPLE_RATE / self.rate)
            samples    = np.interp(np.linspace(0, len(samples) - 1, count), np.arange(len(samples)), samples)

        return samples.astype(np.int16).tobytes()

    # --- start capturing audio

    def start(self):
        self.stream = self.audio.open(
            format            = pyaudio.paInt16,
            channels          = self.channels,
            rate              = self.rate,
            input             = True,
            input_device_index = self.device["index"],
            frames_per_buffer = int(self.rate * BLOCK_SECS),
            stream_callback   = self._capture
        )
        self.running = True
        threading.Thread(target = self._recognise, daemon = True).start()
        print(f"Listening to: {self.name}")

    # --- recognise queued audio

    def _recognise(self):
        while self.running:
            try:
                data = self.q.get(timeout = 0.5)
            except queue.Empty:
                continue

            if self.recognizer.AcceptWaveform(self._convert(data)):
                heard     = json.loads(self.recognizer.Result())
                utterance = heard.get("text", "").strip()
                if utterance:
                    self.callback(utterance)

    # --- stop capturing audio

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

# --- A simple listener class that hears the microphone and the speaker output

class Listener:

    # --- constructor

    def __init__(self, callback):
        self.model    = Model(MODEL_PATH)
        self.callback = callback
        self.audio    = None
        self.sources  = []
        self.running  = False

    # --- start listening

    def start(self):
        if self.running:
            return

        self.audio = pyaudio.PyAudio()
        devices    = []

        try:
            devices.append(self.audio.get_default_input_device_info())
        except Exception as err:
            print(f"Listening: no microphone found ({ err })")

        try:
            devices.append(self.audio.get_default_wasapi_loopback())
        except Exception as err:
            print(f"Listening: no speaker loopback found ({ err })")

        try:
            for device in devices:
                source = Source(self.audio, device, self.model, self.callback)
                source.start()
                self.sources.append(source)

            self.running = True
            while self.running:
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("Listening Closing...")
            self.stop()

        except Exception as err:
            print(f"Listening Error: { err }")
            self.stop()

    # --- stop listening

    def stop(self):
        for source in self.sources:
            source.stop()
        self.sources = []
        if self.audio:
            self.audio.terminate()
            self.audio = None
        self.running = False
        print("Listening Stopped")
