import wave
from pathlib import Path
from typing import Any, Dict

import pyaudio
import whisper


class WhisperASR:
    _shared_models: Dict[str, Any] = {}

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.model_name = str(cfg.get("model_name", "small")).strip() or "small"
        self.language = str(cfg.get("language", "zh")).strip() or "zh"
        self.prompt = str(cfg.get("prompt", "")).strip()
        self.sample_rate = int(cfg.get("sample_rate", 16000))
        self.chunk_size = int(cfg.get("chunk_size", 1024))
        self.record_seconds = float(cfg.get("record_seconds", 5.0))
        self.channels = int(cfg.get("channels", 1))
        self.wav_path = Path(str(cfg.get("wav_path", "temp.wav")).strip() or "temp.wav")

        if self.sample_rate <= 0:
            raise RuntimeError("whisper_asr.sample_rate must be positive")
        if self.chunk_size <= 0:
            raise RuntimeError("whisper_asr.chunk_size must be positive")
        if self.channels != 1:
            raise RuntimeError("local whisper flow currently supports mono audio only")
        if self.record_seconds <= 0:
            raise RuntimeError("whisper_asr.record_seconds must be positive")

    def _get_model(self) -> Any:
        model = self._shared_models.get(self.model_name)
        if model is None:
            model = whisper.load_model(self.model_name)
            self._shared_models[self.model_name] = model
        return model

    def _record_audio(self) -> Path:
        audio = pyaudio.PyAudio()
        sample_width = audio.get_sample_size(pyaudio.paInt16)
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

        frame_count = max(1, int(self.record_seconds * self.sample_rate / self.chunk_size))
        frames: list[bytes] = []

        try:
            for _ in range(frame_count):
                frames.append(stream.read(self.chunk_size, exception_on_overflow=False))
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

        wav_path = self.wav_path
        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(b"".join(frames))

        return wav_path

    def _transcribe_file(self, wav_path: Path) -> str:
        model = self._get_model()
        result = model.transcribe(
            str(wav_path),
            fp16=False,
            language=self.language,
            initial_prompt=self.prompt or None,
            verbose=False,
        )
        return str(result.get("text", "")).strip()

    def transcribe_once(self) -> str:
        wav_path = self._record_audio()
        return self._transcribe_file(wav_path)
