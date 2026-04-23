import whisper
import pyaudio
import wave
import threading
import time
import os
from torch.xpu import device

# 初始化 whisper 模型
model = whisper.load_model("tiny")  # 可选 "small", "medium", "large" 提高准确率
LANGUAGE = "zh"
# 音频配置
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5  # 每段录音时长
AUDIO_OUTPUT = "temp_audio.wav"

def record_audio(filename, duration=5):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("🎙️ 正在录音...")

    frames = []
    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("✅ 录音结束，正在识别...")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))


def transcribe_audio(filename):
    result = model.transcribe(
        filename, 
        fp16=False,
        language=LANGUAGE,
        verbose=False
    )
    print(f"📝 识别结果：{result['text']}")
    return result['text']


def realtime_loop():
    while True:
        record_audio(AUDIO_OUTPUT, duration=RECORD_SECONDS)
        transcribe_audio(AUDIO_OUTPUT)


if __name__ == "__main__":
    try:
        realtime_loop()
    except KeyboardInterrupt:
        print("\n👋 识别结束，程序已退出。")
        if os.path.exists(AUDIO_OUTPUT):
            os.remove(AUDIO_OUTPUT)
