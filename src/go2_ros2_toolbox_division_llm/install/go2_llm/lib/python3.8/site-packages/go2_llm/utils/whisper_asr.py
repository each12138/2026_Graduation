import os

import pyaudio
import wave
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


def record_audio(filename, duration=5):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print("正在录音...")

    frames = []
    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("录音结束，正在识别...")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(filename, "wb") as wave_file:
        wave_file.setnchannels(CHANNELS)
        wave_file.setsampwidth(audio.get_sample_size(FORMAT))
        wave_file.setframerate(RATE)
        wave_file.writeframes(b"".join(frames))


def transcribe_audio(filename):
    asr_model = get_model()
    result = asr_model.transcribe(
        filename,
        fp16=False,
        language=LANGUAGE,
        verbose=False,
    )
    print(f"识别结果：{result['text']}")
    return result["text"]


def realtime_loop():
    while True:
        record_audio(AUDIO_OUTPUT, duration=RECORD_SECONDS)
        transcribe_audio(AUDIO_OUTPUT)


if __name__ == "__main__":
    try:
        realtime_loop()
    except KeyboardInterrupt:
        print("\n识别结束，程序已退出。")
        if os.path.exists(AUDIO_OUTPUT):
            os.remove(AUDIO_OUTPUT)
