import json
import requests

# --- constants

LLM_URL = "http://localhost:11434/api/generate" # ollama api endpoint
MODEL_NAME = "qwen3.5:9b"
CONTEXT_SIZE = 4096 # small context keeps the model fully on the gpu
TRANSCRIPT_WORDS = 1500 # most recent words sent to the model - leaves room in the context for the instructions and reply

# --- trims a transcript to its most recent words

def trim(text, max_words = TRANSCRIPT_WORDS):
    words = text.split()
    return " ".join(words[-max_words:])

# --- A simple text analysis class

class Analyser:

    # --- constructor

    def __init__(self, cue = ""):
        self.context(cue)

    # --- changes the context

    def context(self, cue = ""):
        self.cue = cue

    # --- analyse an utterance

    def analyse(self, utterance):
        utterance = trim(utterance)
        if not utterance:
            return []

        try:
            response = requests.post(
                LLM_URL,
                json = {
                    "model":  MODEL_NAME,
                    "prompt": self._prompt(utterance),
                    "stream": False,
                    "think":  False,
                    "options": { "num_ctx": CONTEXT_SIZE }
                }
            )

            result = response.json().get("response", "")
            result = result.replace("```json", "").replace("```", "").strip() # remove common litter
            return json.loads(result)

        except Exception as err:
            print(f"Analysis Error: { err }")
            return []

    # --- generates a prompt from an utterance

    def _prompt(self, utterance):
        return f"""
You are the listener's secret side-kick in a live conversation. You help them contribute with accurate, specific and useful points.

You are given an automatic transcript of the conversation. It mixes everyone who is speaking, including the listener, and has no speaker labels. It may contain misheard words, such as "kabir nets" for "Kubernetes". Work out the intended meaning from context, and ignore anything you cannot interpret rather than guessing.

Focus on the most recent part of the conversation, which is at the end of the text. Earlier text is only context.

Return a JSON array of 2 to 4 entries. Each entry must be one of these types:

* Information | type: "understand"  | a concise definition or overview of a key topic, term or idea mentioned in the conversation
* Theme       | type: "contribute" | a relevant point the listener could add - written in the first person as a direct quote, e.g. "In my experience, ..."
* Challenge   | type: "challenge"  | a respectful challenge or probing question the listener could put to the speaker - written as a direct quote, e.g. "What evidence do we have that ...?"

Rules:
* "name" is a short, specific title for the topic, such as "Kubernetes" or "Migration risk" - never generic such as "Insight" or "Question"
* every "name" must be unique within the array
* "text" is a single paragraph of at most 32 words
* do not repeat or restate what was just said - add something new
* be factual - do not invent statistics, quotes or sources

Format:
[
    {{ "type": "understand", "name": "<specific topic title>", "text": "<at most 32 words>" }},
    more such entries...
]

All output must be valid JSON - no other commentary or explanation.

{ self.cue }

Transcript: { json.dumps(utterance) }
"""
