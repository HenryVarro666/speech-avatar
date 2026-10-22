"""Decode every output and compare its audio with the frozen source waveform."""
import array
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import statistics
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/2026-10-20-e1-musetalk"


def correlation(a, b):
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    sx, sy = sum(a), sum(b)
    covariance = n * sum(x * y for x, y in zip(a, b)) - sx * sy
    variance = (n * sum(x * x for x in a) - sx * sx) * (n * sum(y * y for y in b) - sy * sy)
    return covariance / math.sqrt(variance) if variance > 0 else 0


def main():
    rows = [json.loads(line) for line in (EXPERIMENT / "trials.jsonl").read_text().splitlines()]
    verdict_path = EXPERIMENT / "quality_verdict.json"
    verdict = json.loads(verdict_path.read_text()) if verdict_path.exists() else None
    review_path = EXPERIMENT / "quality_review.csv"
    reviews = {r["trial_id"]: r for r in csv.DictReader(review_path.open())} if review_path.exists() else {}
    checks, strips, cards = [], [], []
    qa = ROOT / "outputs/qa"
    qa.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = ROOT / row["output_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["output_sha256"]:
            raise ValueError(f"Output hash changed: {row['trial_id']}")
        subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"], capture_output=True, check=True)
        probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
        video = next(s for s in probe["streams"] if s["codec_type"] == "video")
        decoded = array.array("h", subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]))
        with wave.open(str(ROOT / row["audio_path"]), "rb") as stream:
            original = array.array("h", stream.readframes(stream.getnframes()))
        a, b = original[::16], decoded[::16]
        values = []
        for lag in range(-32, 33):
            values.append((correlation(a if lag >= 0 else a[-lag:], b[lag:] if lag >= 0 else b), lag))
        best, lag = max(values)
        delta = (len(decoded) - len(original)) / 16
        checks.append({"trial_id": row["trial_id"], "full_decode": "passed", "width": video["width"],
                       "height": video["height"], "fps": video["avg_frame_rate"],
                       "video_frames": int(video["nb_frames"]), "decoded_audio_duration_s": len(decoded) / 16000,
                       "decoded_audio_duration_delta_ms": delta, "zero_lag_correlation": correlation(a, b),
                       "best_correlation": best, "best_audio_lag_ms": lag,
                       "audio_integrity_check": best >= 0.95 and abs(lag) <= 20 and -20 <= delta <= 100})
        count = int(video["nb_frames"])
        indices = [0, count // 4, count // 2, count * 3 // 4]
        select = "+".join(f"eq(n,{i})" for i in indices)
        strip = qa / (row["trial_id"] + ".png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vf", f"select='{select}',scale=256:256,tile=4x1", "-frames:v", "1", str(strip)], capture_output=True, check=True)
        strips.append(strip)
        review = reviews.get(row["trial_id"])
        note = "Offline, fictional still-reference avatar. Visual and audio-sync review pending."
        if review:
            note = (f'SyncNet estimate: {review["syncnet_offset_ms"]} ms (video leads audio). '
                    f'Inspect {review["teeth_observation_time_s"]} s: {review["teeth_and_lips_notes"]} '
                    f'{review["ending_notes"]} Human AV rating: unrated.')
        cards.append(f'<section><h2>{html.escape(row["trial_id"])}</h2><video controls preload="metadata" width="360" src="v15/{html.escape(path.name)}"></video><p>{html.escape(note)}</p></section>')
    ffmpeg = ["ffmpeg", "-y", "-v", "error"]
    for strip in strips:
        ffmpeg += ["-i", str(strip)]
    ffmpeg += ["-filter_complex", f"vstack=inputs={len(strips)}", "-frames:v", "1", str(qa / "all-trials.png")]
    subprocess.run(ffmpeg, capture_output=True, check=True)
    status = '<p><strong>Quality audit: NEEDS WORK / not signed off.</strong> 12/12 browser playback; 1,032 mouth frames inspected. SyncNet estimates video leads audio by 80–120 ms. Soft teeth, incomplete neutral endings and static head/eyes need review. These are assistant visual observations and model estimates; human continuous audio-visual ratings are absent. No perceptual pass count is claimed.</p>' if verdict else ''
    (ROOT / "outputs/e1/index.html").write_text('<!doctype html><meta charset="utf-8"><title>E1 offline review</title><style>body{font:16px system-ui;margin:24px;background:#eef1f5}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px}section{background:white;padding:16px;border-radius:10px}h2{font-size:16px}</style><h1>MuseTalk E1 offline review</h1><p>12 fixed pairs. Decoding and audio checks do not establish visual acceptability. No live microphone or conversation latency claim.</p>' + status + '<main>' + ''.join(cards) + '</main>')
    data = {"trials": len(rows), "rendered": sum(r["status"] == "rendered_pending_review" for r in rows),
            "full_decode_passed": len(checks), "audio_integrity_passed": sum(c["audio_integrity_check"] for c in checks),
            "wall_s_median": statistics.median(r["wall_s"] for r in rows),
            "first_saved_frame_s_median": statistics.median(r["first_saved_frame_s"] for r in rows),
            "rtf_median": statistics.median(r["rtf"] for r in rows),
            "post_first_trial_wall_s_median": statistics.median(r["wall_s"] for r in rows[1:]),
            "max_peak_torch_allocated_mib": max(r["peak_torch_allocated_mib"] for r in rows),
            "max_peak_torch_reserved_mib": max(r["peak_torch_reserved_mib"] for r in rows),
            "visual_acceptability": verdict["overall_disposition"] if verdict else "pending_continuous_playback_and_human_review",
            "quality_verdict_file": "quality_verdict.json" if verdict else None, "checks": checks}
    (EXPERIMENT / "validation.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k != "checks"}, indent=2))


if __name__ == "__main__":
    main()
