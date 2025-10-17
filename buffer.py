import time
import json
import threading
from collections import deque

# --- A simple thread-safe rolling review buffer class

class ReviewBuffer:

    # --- constructor

    def __init__(self, max_age = 60):
        self.max_age = max_age         # max age of items in seconds
        self.entries = deque()         # stores (timestamp, name, meta, text)
        self.lock = threading.Lock()   # for thread-safe access

    # --- flush out expired entries

    def _flush(self):
        cutoff = time.time() - self.max_age
        while self.entries and self.entries[0][0] < cutoff:
            self.entries.popleft()

    # --- remove an item by name (if it exists)

    def remove(self, name):
        with self.lock:
            self._flush()
            for i, entry in enumerate(self.entries):
                if entry[1] == name:
                    del self.entries[i]
                    break

    # --- append a new item to the buffer

    def add(self, text, meta = None, name = None): # meta and name are optional
        with self.lock:
            self._flush()
            if name:
                for i, entry in enumerate(self.entries):
                    if entry[1] == name:
                        del self.entries[i]
                        break
            self.entries.append((time.time(), name, meta, text))

    # --- returns all the texts as a single string

    @property
    def text(self):
        with self.lock:
            self._flush()
            return ' '.join(text for _, name, _, text in self.entries)

    # --- returns all the names and texts as an array

    @property
    def list(self):
        with self.lock:
            self._flush()
            return [(name, text) for _, name, _, text in self.entries]

    # --- returns all the entries as json array of objects

    @property
    def items(self):
        with self.lock:
            self._flush()
            return json.dumps([
                {"time": ts, "name": name, "meta": meta, "text": text}
                for ts, name, meta, text in self.entries
            ], ensure_ascii=False, indent=2)

    # --- clears out the review buffer

    def clear(self):
        with self.lock:
            self.entries.clear()
