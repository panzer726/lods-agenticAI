import tensorflow as tf
import numpy as np
import sounddevice as sd
import librosa
import time
from collections import deque

import tinytuya
light = tinytuya.OutletDevice('a36cb72light1945cf9235fcsy', '192.168.1.2', 'Ke;0MYt#GGtwb?+u')
light.set_version(3.5)

model = tf.saved_model.load('./yamnet_local')
class_map_path = model.class_map_path().numpy()
class_names = [line.split(',')[2] for line in open(class_map_path).read().splitlines()[1:]]
clap_index = class_names.index('Clapping')

NATIVE_RATE = 44100
TARGET_RATE = 16000
WINDOW_SECONDS = 1.0
BUFFER_SECONDS = 2.0
THRESHOLD = 0.005
COOLDOWN = 0.4        
DOUBLE_CLAP_WINDOW = 1.0  

buffer = deque(maxlen=int(BUFFER_SECONDS * NATIVE_RATE))

def audio_callback(indata):
    buffer.extend(indata[:, 0])

stream = sd.InputStream(samplerate=NATIVE_RATE, channels=1, dtype='float32', callback=audio_callback)
stream.start()

last_clap = 0
clap_times = []

print("Listening for claps...")

while True:
    time.sleep(0.2)

    if len(buffer) < int(WINDOW_SECONDS * NATIVE_RATE):
        continue

    waveform_native = np.array(list(buffer)[-int(WINDOW_SECONDS * NATIVE_RATE):])
    waveform = librosa.resample(waveform_native, orig_sr=NATIVE_RATE, target_sr=TARGET_RATE)

    scores, embeddings, spectrogram = model(waveform)
    max_scores = np.max(scores.numpy(), axis=0)
    clap_score = max_scores[clap_index]

    now = time.time()

    if clap_score > THRESHOLD and (now - last_clap) > COOLDOWN:
        last_clap = now
        clap_times.append(now)
        print(f"Clap detected (score {clap_score:.4f})")

        clap_times = [t for t in clap_times if now - t <= DOUBLE_CLAP_WINDOW]

        if len(clap_times) >= 3:
            print(">>> TRIPLE CLAP DETECTED <<<")
            light.set_value(20, True)
            time.sleep(0.2)
            light.set_value(21, "white")
            time.sleep(0.2)
            light.set_value(22, 1000)
            time.sleep(0.2)
            light.set_value(23, 800)   
            clap_times = []

        elif len(clap_times) == 2:
            print(">>> DOUBLE CLAP DETECTED <<<")
            state = light.status()['dps']['20']
            print(state)
            light.set_value(20, not state)
            clap_times = [] 