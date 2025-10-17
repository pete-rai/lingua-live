import json
import requests

# --- constants

LLM_URL = "http://localhost:11434/api/generate" # ollama api endpoint
MODEL_NAME = "wizardlm2:7b"
# MODEL_NAME = "llama3.1:latest"

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
        if not utterance.strip():
            return []

        try:
            response = requests.post(
                LLM_URL,
                json = {
                    "model":  MODEL_NAME,
                    "prompt": self._prompt(utterance),
                    "stream": False
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
You are given transcribed speech that may include misheard words. Use the full context to correct obvious transcription errors.

Your role is to analyse the text to provide short, punchy, insightful comments to a listener.

You are the listener's secret side-kick and your purpose is to make them look good and make them appear knowledgeable and wise.

In your analysis you will return a JSON array where each entry is one of the following types:

* Information | type: "understand" | concise definition or overvier of a key topic, item or theme that is mentioned in the text
* Theme       | type: "contribute" | quick things that the listener can add to the conversation - worded as a direct quote that the listener can add
* Challenge   | type: "challenge"  | a quick challenge that the listener can give the speaker - worded as a quote that the listener can ask

Format:
[
    {{{{ "type": "<one from the listed items above>", "name": "<a non-empty item name>", "text": "<a paragraph of maximum of 32 words>" }}}},
    more such items...
]

All output must be valid JSON - no other commentary or explanation.

{ self.cue }

Speaker text is: { json.dumps(utterance) }
"""
