"""Verify frozen waveforms, provenance and split integrity without ML dependencies."""
import argparse
import array
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import wave


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_rows(rows, root):
    families, hashes, ids, texts = {}, set(), set(), set()
    stats = []
    for row in rows:
        ident = row["id"]
        if ident in ids:
            raise ValueError(f"duplicate id: {ident}")
        ids.add(ident)
        family, split = row["family_id"], row["split"]
        if family in families and families[family] != split:
            raise ValueError(f"family crosses splits: {family}")
        families[family] = split
        text_key = (row["language"], "".join(row["text"].lower().split()))
        if text_key in texts:
            raise ValueError(f"duplicate text: {ident}")
        texts.add(text_key)
        if not row.get("provenance", {}).get("generator") or not row["provenance"].get("kind"):
            raise ValueError(f"missing provenance: {ident}")
        path = (root / row["audio_path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError(f"media outside root: {ident}")
        digest = sha256(path)
        if digest != row["sha256"]:
            raise ValueError(f"hash mismatch: {ident}")
        if digest in hashes:
            raise ValueError(f"duplicate audio hash: {ident}")
        hashes.add(digest)
        with wave.open(str(path), "rb") as stream:
            if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()) != (1, 2, 16000):
                raise ValueError(f"expected mono PCM16 16kHz: {ident}")
            count = stream.getnframes()
            samples = array.array("h", stream.readframes(count))
        if sys.byteorder != "little":
            samples.byteswap()
        duration = count / 16000
        if not 2 <= duration <= 15:
            raise ValueError(f"duration outside 2-15s: {ident} ({duration})")
        peak = max(abs(v) for v in samples) / 32768
        if peak < 0.01:
            raise ValueError(f"silent input: {ident}")
        stats.append({"id": ident, "duration_s": duration, "samples": count, "peak": peak,
                      "rms": (sum((v / 32768) ** 2 for v in samples) / len(samples)) ** 0.5})
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    frozen_hash = args.manifest.with_suffix(".sha256").read_text().split()[0]
    if sha256(args.manifest) != frozen_hash:
        raise ValueError("frozen manifest hash mismatch")
    manifest = json.loads(args.manifest.read_text())
    rows = manifest["audio"]
    counts = Counter((r["split"], r["language"]) for r in rows)
    expected = {("dev", "en"): 6, ("dev", "zh"): 6, ("test", "en"): 12, ("test", "zh"): 12}
    if counts != expected:
        raise ValueError(f"split counts differ: {counts}")
    for split, lang in expected:
        voices = Counter(r["voice"] for r in rows if (r["split"], r["language"]) == (split, lang))
        if len(voices) != 2 or len(set(voices.values())) != 1:
            raise ValueError(f"voice imbalance: {split}/{lang}: {voices}")
    stats = validate_rows(rows, args.root)
    if len(manifest["avatars"]) != 2:
        raise ValueError("two avatars required")
    for avatar in manifest["avatars"]:
        if not avatar.get("provenance", {}).get("prompt"):
            raise ValueError("avatar provenance missing")
        for media in avatar["files"]:
            if sha256(args.root / media["path"]) != media["sha256"]:
                raise ValueError(f"avatar hash mismatch: {media['path']}")
    result = {"status": "passed", "audio_count": len(rows), "avatars": 2,
              "manifest_sha256": sha256(args.manifest), "audio_stats": stats}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
