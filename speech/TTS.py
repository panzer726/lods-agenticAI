import os
import json
import numpy as np
import sounddevice as sd
from piper import PiperVoice
from piper.config import SynthesisConfig

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'en_GB-alan-medium.onnx')
CONFIG_PATH = os.path.join(BASE_DIR, 'en_GB-alan-medium.onnx.json')

with open(CONFIG_PATH, encoding='utf-8') as f:
    config = json.load(f)

voice = PiperVoice.load(MODEL_PATH, config_path=CONFIG_PATH)
def speak(text):
    audio_chunks = voice.synthesize(text)
    audio = np.concatenate([
        np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
        for chunk in audio_chunks
    ])

    silence = np.zeros(int(0.3 * voice.config.sample_rate), dtype=np.int16)
    audio = np.concatenate([audio, silence])

    sd.play(audio, samplerate=voice.config.sample_rate)
    sd.wait()