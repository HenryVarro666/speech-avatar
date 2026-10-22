"""Compare references, first/last frames and decoded audio tails locally."""
import json
import numpy as np
from PIL import Image, ImageDraw
from audit_e1_quality import ROOT, EXP, audio, read_video


def main():
    rows = [json.loads(x) for x in (EXP / "trials.jsonl").read_text().splitlines()]
    sheet = Image.new("RGB", (768, len(rows)*284), "white")
    draw = ImageDraw.Draw(sheet)
    meta = []
    for j, row in enumerate(rows):
        frames = read_video(ROOT / row["output_path"])
        ref = read_video(ROOT / row["video_path"])[0]
        for k, (frame, label) in enumerate([
                (ref, "reference"), (frames[0], "first frame"),
                (frames[-1], f"last {(len(frames)-1)/25:.2f}s")]):
            sheet.paste(Image.fromarray(frame[:, :, ::-1]).resize((256, 256)), (k*256, j*284+28))
            draw.text((k*256+4, j*284+12), row["trial_id"]+" "+label, fill="black")
        pcm = audio(ROOT / row["output_path"]).astype(np.float64)/32768
        tail = pcm[-3200:]
        meta.append({"trial_id": row["trial_id"],
                     "last_video_frame_s": (len(frames)-1)/25,
                     "audio_duration_s": len(pcm)/16000,
                     "last_200ms_all_samples_zero": bool(np.all(tail == 0)),
                     "last_200ms_rms_dbfs": float(20*np.log10(max(1e-12, np.sqrt(np.mean(tail**2))))),
                     "note": "dBFS floor -240; RMS alone is not a phoneme or human silence label."})
    sheet.save(ROOT / "outputs/quality/reference-first-last.png")
    (EXP / "quality_endings.json").write_text(json.dumps(meta, indent=2)+"\n")
    print(f"Compared {len(rows)} endings")


if __name__ == "__main__":
    main()
