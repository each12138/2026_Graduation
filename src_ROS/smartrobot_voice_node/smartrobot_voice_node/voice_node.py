from .whisper_asr import AUDIO_OUTPUT, cleanup_audio_file, record_audio, transcribe_audio


class VoiceNode:
    """Voice input node boundary.

    Current runtime supports both keyboard text and whisper capture.
    """

    def __init__(self, use_whisper=False, record_seconds=5):
        self.use_whisper = bool(use_whisper)
        self.record_seconds = int(record_seconds)

    def read_user_text(self):
        if not self.use_whisper:
            return input("User command: ").strip()

        record_audio(AUDIO_OUTPUT, duration=self.record_seconds)
        text = transcribe_audio(AUDIO_OUTPUT).strip()
        cleanup_audio_file(AUDIO_OUTPUT)
        return text
