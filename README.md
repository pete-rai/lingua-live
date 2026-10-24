# LinguaLive

Your secret side-kick for live conversations. LinguaLive listens to your microphone and to the sound playing through your speakers (such as the other people in a Google Meet or Zoom call), transcribes it locally, and uses a local language model to suggest short, useful comments in your browser as the conversation unfolds.

Everything runs on your own machine. No audio or text is sent to a cloud service.

## What you get

Each insight appears as a card, colour-coded by type:

| Type | Colour | Purpose |
|------|--------|---------|
| **Understand** | Blue | A concise definition or overview of a topic that was mentioned |
| **Contribute** | Green | Something you could add to the conversation, worded as a quote |
| **Challenge** | Red | A question you could put to the speaker, worded as a quote |

Cards can be dismissed individually and expire automatically after four minutes.

## How it works

```
Microphone + speaker loopback -> Vosk (speech to text) -> Ollama (analysis) -> Flask server -> Browser cards
```

1. [listen.py](listen.py) captures your default microphone and the default speaker output (WASAPI loopback), and transcribes each offline with [Vosk](https://alphacephei.com/vosk/). Loopback capture is unaffected by echo cancellation on speakerphones, so remote participants are heard even on a device like the Anker PowerConf.
2. [main.py](main.py) keeps the last three minutes of speech and sends it to the analyser after each new utterance.
3. [analyse.py](analyse.py) asks a model running in [Ollama](https://ollama.com/) for insights, returned as JSON.
4. [buffer.py](buffer.py) holds the rolling transcript and insights, with expiry.
5. [static/index.html](static/index.html) polls the server every three seconds and shows the cards.

## Requirements

- Python 3.9 or later
- Windows (speaker capture uses WASAPI loopback)
- A working microphone
- [Ollama](https://ollama.com/) running locally with a model installed
- A Vosk speech model (see below)
- A GPU is recommended for responsive analysis

## Setup

1. **Create an environment and install dependencies**

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install flask requests numpy PyAudioWPatch vosk
   ```

2. **Download a Vosk model.** Get `vosk-model-small-en-us-0.15` from the [Vosk models page](https://alphacephei.com/vosk/models) and unzip it into the `model` folder, so the path is `model/vosk-model-small-en-us-0.15`.

3. **Install an Ollama model.** Pull the model named by `MODEL_NAME` in [analyse.py](analyse.py), or change that setting to a model you already have:

   ```powershell
   ollama pull qwen3.5:9b
   ollama list
   ```

   You can check that Ollama is running with `Invoke-RestMethod http://localhost:11434/api/tags`.

## Running

```powershell
python main.py
```

Then open <http://localhost:8001> and start talking. The console prints each transcribed utterance and how long each analysis took.

## Using the interface

- **Pencil button** sets extra instructions for the model, for example "All text should be in French". Applying them clears the current cards.
- **Bin button** clears all cards and the transcript buffer.
- **X on a card** removes that card.

## Configuration

| Setting | File | Default |
|---------|------|---------|
| Ollama model | [analyse.py](analyse.py) | `qwen3.5:9b` |
| Model context size | [analyse.py](analyse.py) | 4096 tokens |
| Transcript words sent to the model | [analyse.py](analyse.py) | 1500 (most recent) |
| Ollama URL | [analyse.py](analyse.py) | `http://localhost:11434/api/generate` |
| Speech model path | [listen.py](listen.py) | `model/vosk-model-small-en-us-0.15` |
| Transcript depth | [main.py](main.py) | 3 minutes |
| Card lifetime | [main.py](main.py) | 4 minutes |
| Server port | [main.py](main.py) | `8001` |

## Tips

- The small Vosk model is fast but less accurate with accents and noise. Larger Vosk models are available if you need better recognition.
- Check `ollama ps` to confirm your model runs fully on the GPU. The app requests a 4096-token context so the model fits in GPU memory; a very large window can push part of it onto the CPU and slow analysis.
- The server listens on all network interfaces (`0.0.0.0`) and has no authentication. Use it only on a network you trust.

## Licence

Released under the [MIT License](LICENSE).
