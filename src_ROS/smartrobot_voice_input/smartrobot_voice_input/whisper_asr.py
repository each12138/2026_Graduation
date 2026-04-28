import os
import wave

import pyaudio
import whisper

model = None
LANGUAGE = "zh"
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5
AUDIO_OUTPUT = "temp_audio.wav"


def get_model():
    global model
    if model is None:
        model = whisper.load_model("tiny")
    return model


def record_audio(filename, duration=RECORD_SECONDS):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    frames = []
    for _ in range(0, int(RATE / CHUNK * duration)):
        frames.append(stream.read(CHUNK))
    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))


def transcribe_audio(filename):
    asr_model = get_model()
    result = asr_model.transcribe(filename, fp16=False, language=LANGUAGE, verbose=False)
    print(f"📝 识别结果：{result['text']}")
    return result["text"]


def cleanup_audio_file(path=AUDIO_OUTPUT):
    if os.path.exists(path):
        os.remove(path)
