"""Prepare local synthetic input waveforms and freeze a metadata manifest."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import wave

from validate_e0 import sha256, validate_rows

ROOT = Path(__file__).resolve().parents[1]


def run(command):
    subprocess.run(command, check=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/2026-10-20-e0/manifest.json")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite a frozen manifest; choose a versioned output.")
    corpus_path = ROOT / "assets/corpus.json"
    corpus = json.loads(corpus_path.read_text())
    rows = []
    for split in ("dev", "test"):
        for lang in ("en", "zh"):
            for index, (feature, text) in enumerate(corpus[split][lang], 1):
                ident = f"{split}-{lang}-{index:02d}"
                voice = corpus["voices"][lang][(index - 1) % 2]
                base = ROOT / "data/private/audio" / split / ident
                base.parent.mkdir(parents=True, exist_ok=True)
                text_path, source, wav_path = base.with_suffix(".txt"), base.with_suffix(".aiff"), base.with_suffix(".wav")
                text_path.write_text(text + "\n")
                command = ["say", "-v", voice, "-r", "160" if lang == "en" else "180", "-f", str(text_path), "-o", str(source)]
                if not source.exists():
                    run(command)
                if not wav_path.exists():
                    run(["ffmpeg", "-v", "error", "-i", str(source), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav_path)])
                with wave.open(str(wav_path), "rb") as stream:
                    count = stream.getnframes()
                row = {"id": ident, "family_id": ident, "split": split, "language": lang,
                       "feature": feature, "voice": voice, "text": text, "audio_path": str(wav_path.relative_to(ROOT)),
                       "sha256": sha256(wav_path), "source_sha256": sha256(source), "source_path": str(source.relative_to(ROOT)),
                       "sample_rate": 16000, "channels": 1, "format": "s16le", "sample_count": count,
                       "duration_s": count / 16000, "crop": {"start_sample": 0, "end_sample": count, "kind": "none"},
                       "transcript": {"text": text, "source": "synthesis_input", "human_verified": False},
                       "provenance": {"kind": "synthetic", "generator": "macOS /usr/bin/say", "platform": platform.platform(),
                                      "voice": voice, "command": command, "redistribution": "not_reviewed_private_only"}}
                rows.append(row)
                print(f"{ident}: {count / 16000:.2f}s", flush=True)
    stats = validate_rows(rows, ROOT)
    avatars = json.loads((ROOT / "assets/avatars.json").read_text())["avatars"]
    manifest = {"schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "corpus_sha256": sha256(corpus_path), "family_definition": corpus["family_definition"],
                "audio": rows, "avatars": avatars, "validation_stats": stats,
                "limits": ["synthetic speech only", "transcripts are synthesis inputs, not human listening labels",
                           "fictional still-image avatar references", "not native speech model or microphone trials"]}
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    args.output.with_suffix(".sha256").write_text(f"{sha256(args.output)}  {args.output.name}\n")


if __name__ == "__main__":
    main()
