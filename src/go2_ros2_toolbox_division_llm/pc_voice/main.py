import json
import msvcrt
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict

import yaml

from .bridge_client import DogBridgeClient
from .whisper_asr import WhisperASR


def load_config(path: str | Path) -> Dict[str, Any]:
    cfg_path = Path(path)
    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise RuntimeError("config root must be a mapping")

    for required_key in ("bridge", "whisper_asr"):
        if required_key not in data:
            raise RuntimeError(f"missing config section: {required_key}")

    return data


def wait_until_unmuted(bridge: DogBridgeClient, interval_s: float = 0.5) -> None:
    last_reason = None

    while True:
        state = bridge.get_state()
        if not state.muted:
            if last_reason is not None:
                print("[state] microphone unmuted")
            return

        if state.reason != last_reason:
            print(f"[state] muted by dog-side state: {state.reason}")
            last_reason = state.reason

        time.sleep(interval_s)


def wait_for_space_trigger(bridge: DogBridgeClient) -> str | None:
    print("[trigger] press Space to start recording...")

    while True:
        state = bridge.get_state()
        if state.muted:
            return None

        if msvcrt.kbhit():
            key = msvcrt.getwch()
            if key == " ":
                return f"sess_{uuid.uuid4().hex[:12]}"

        time.sleep(0.05)


def main() -> None:
    cfg_path = Path(__file__).resolve().parent / "config" / "pc_voice.yaml"
    cfg = load_config(cfg_path)

    bridge = DogBridgeClient(cfg["bridge"])
    transcriber = WhisperASR(cfg["whisper_asr"])

    print("PC voice client started.")
    print("Press Space to trigger a fixed-length local Whisper recording.")
    print("Input is disabled while the dog is navigating or speaking.")

    while True:
        wait_until_unmuted(bridge)

        session_id = wait_for_space_trigger(bridge)
        if session_id is None:
            continue

        state = bridge.get_state()
        if state.muted:
            print(f"[state] rejected before recording: {state.reason}")
            continue

        print("[whisper] recording now...")
        utterance_id = f"utt_{uuid.uuid4().hex[:12]}"

        try:
            transcript = transcriber.transcribe_once()
        except Exception as exc:
            print(f"[whisper] failed: {exc}")
            continue

        if not transcript:
            print("[whisper] empty transcript")
            continue

        print(f"[asr] {transcript}")

        try:
            result = bridge.post_text(transcript, session_id, utterance_id)
        except Exception as exc:
            print(f"[bridge] send failed: {exc}")
            continue

        if not bool(result.get("ok", False)):
            print(f"[bridge] rejected: {json.dumps(result, ensure_ascii=False)}")
            continue

        print(f"[bridge] sent request_id={result.get('request_id', '')}")

if __name__ == "__main__":
    main()
