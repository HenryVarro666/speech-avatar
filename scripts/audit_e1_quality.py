"""Local CPU SyncNet diagnostics and chronological all-frame visual evidence.

Requires the separately installed .venv-quality and official, ignored SyncNet source
and weights. Does not modify source media or the frozen render ledger.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw
import python_speech_features
import torch

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/2026-10-20-e1-musetalk"
VENDOR = ROOT / "vendor/syncnet_python"
sys.path.insert(0, str(VENDOR))
from SyncNetModel import S
from SyncNetInstance import calc_pdist
from detectors import S3FD


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_video(path):
    cap = cv2.VideoCapture(str(path))
    assert cap.get(cv2.CAP_PROP_FPS) == 25
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    return np.stack(frames)


def audio(path):
    return np.frombuffer(subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000",
        "-f", "s16le", "-"], stderr=subprocess.PIPE), dtype="<i2")


def features(model, frames, wav):
    # Same BGR float and default MFCC inputs as official SyncNetInstance.evaluate.
    mfcc = python_speech_features.mfcc(wav, 16000).T
    last = min(len(frames), len(wav) // 640) - 5
    im = torch.from_numpy(frames.transpose(3, 0, 1, 2).copy()).float()[None]
    au = torch.from_numpy(mfcc.copy()).float()[None, None]
    vf, af = [], []
    with torch.inference_mode():
        for start in range(0, last, 8):
            ids = range(start, min(start + 8, last))
            vf.append(model.forward_lip(torch.cat([im[:, :, i:i+5] for i in ids])))
            af.append(model.forward_aud(torch.cat([au[:, :, :, i*4:i*4+20] for i in ids])))
    return torch.cat(vf), torch.cat(af)


def official_score(vf, af):
    curve = torch.stack(calc_pdist(vf, af, vshift=15), 1).mean(1)
    idx = int(curve.argmin())
    return {"offset_frames": 15-idx, "offset_ms": (15-idx)*40,
            "minimum_distance": float(curve[idx]),
            "confidence": float(curve.median()-curve[idx]),
            "distance_curve": curve.tolist()}


def controls(vf, af):
    # Delay d means delayed_af[t] = original_af[t-d]. Use the same common valid
    # visual windows for every delay and candidate; no wraparound/zero padding.
    margin = 25
    stop = min(len(vf), len(af))-margin
    ids = torch.arange(margin, stop)
    if len(ids) < 8:
        raise ValueError("Too few common valid windows for shift controls")
    result = []
    for delay in [0, -10, 10]:
        curve = torch.stack([
            torch.nn.functional.pairwise_distance(vf[ids], af[ids+j-delay]).mean()
            for j in range(-15, 16)])
        offset = 15-int(curve.argmin())
        result.append({"audio_delay_frames": delay, "offset_frames": offset,
                       "confidence": float(curve.median()-curve.min()),
                       "valid_windows": len(ids)})
    base = result[0]["offset_frames"]
    for r in result:
        r["expected_from_baseline"] = base-r["audio_delay_frames"]
        r["recovery_error_frames"] = r["offset_frames"]-r["expected_from_baseline"]
    return result


def face_crops(frames, bbox):
    x1, y1, x2, y2 = bbox
    bs = max(x2-x1, y2-y1)/2
    cx, cy = (x1+x2)/2, (y1+y2)/2
    pad = int(bs*1.8)
    result = []
    for image in frames:
        padded = np.pad(image, ((pad, pad), (pad, pad), (0, 0)),
                        constant_values=110)
        x, y = cx+pad, cy+pad
        crop = padded[int(y-bs):int(y+bs*1.8), int(x-bs*1.4):int(x+bs*1.4)]
        result.append(cv2.resize(crop, (224, 224)))
    return np.stack(result)


def visual_evidence(frames, trial, out):
    # Fixed display crop includes nose base, lips, jaw and surrounding skin.
    # It is unrelated to the face crop used for model scoring.
    rect = (170, 270, 342, 400) if trial.startswith("avatar-a") else (165, 260, 347, 400)
    x1, y1, x2, y2 = rect
    tiles = []
    for i, frame in enumerate(frames):
        tile = Image.new("RGB", (172, 152), "white")
        tile.paste(Image.fromarray(cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2RGB)).resize((172, 130)), (0, 22))
        ImageDraw.Draw(tile).text((3, 3), f"f{i:03d}  {i/25:.2f}s", fill="black")
        tiles.append(tile)
    sheet = Image.new("RGB", (172*8, 152*math.ceil(len(tiles)/8)), "#ddd")
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % 8)*172, (i // 8)*152))
    sheet.save(out / f"{trial}-all-mouths.png")
    differences = np.abs(np.diff(frames.astype(np.int16), axis=0))
    mouth_delta = differences[:, y1:y2, x1:x2].mean(axis=(1,2,3))
    eyes_delta = differences[:, 160:240, 150:360].mean(axis=(1,2,3))
    return {"decoded_frames": len(frames), "visual_crop_xyxy": rect,
            "mouth_adjacent_frame_mae_mean": float(mouth_delta.mean()),
            "eye_region_adjacent_frame_mae_mean": float(eyes_delta.mean()),
            "largest_mouth_change_frame": int(mouth_delta.argmax()+1),
            "largest_mouth_change_time_s": (int(mouth_delta.argmax())+1)/25,
            "largest_mouth_change_mae": float(mouth_delta.max())}


def main():
    torch.set_num_threads(4)
    out = ROOT / "outputs/quality"
    out.mkdir(parents=True, exist_ok=True)
    ledger = EXP / "quality_metrics.json"
    if ledger.exists():
        raise FileExistsError("Keep previous audit; select a new run path before rerunning")
    model = S().eval()
    weights = ROOT / "models/syncnet/syncnet_v2.model"
    model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True))
    # Pin first-frame boxes before any avatar scores; official relative weight path.
    cwd = os.getcwd()
    os.chdir(VENDOR)
    detector = S3FD(device="cpu")
    os.chdir(cwd)
    boxes = {}
    for avatar in ["avatar-a", "avatar-b"]:
        first = read_video(ROOT / f"outputs/e1/v15/{avatar}-dev-en-01.mp4")[0]
        found = detector.detect_faces(cv2.cvtColor(first, cv2.COLOR_BGR2RGB), conf_th=0.9, scales=[0.25])
        if len(found) != 1:
            raise ValueError(f"Expected one first-frame face: {avatar}: {found}")
        boxes[avatar] = found[0, :4].tolist()
    (EXP / "quality_face_boxes.json").write_text(json.dumps(boxes, indent=2)+"\n")
    rows = [json.loads(l) for l in (EXP / "trials.jsonl").read_text().splitlines()]
    data = {"reviewer": "assistant_visual_frames_and_objective_syncnet_not_human_listening",
            "device": "local_cpu_4_threads", "torch_version": torch.__version__,
            "syncnet_commit": subprocess.check_output(["git", "-C", str(VENDOR), "rev-parse", "HEAD"], text=True).strip(),
            "script_sha256": sha(__file__), "weights_sha256": sha(weights),
            "face_detector_sha256": sha(VENDOR / "detectors/s3fd/weights/sfd_face.pth"),
            "official_example_sha256": sha(ROOT / "models/syncnet/example.avi"),
            "official_example": None, "trials": []}
    # Reproduce the official example with our equivalent feature extraction too.
    example = ROOT / "models/syncnet/example.avi"
    vf, af = features(model, read_video(example), audio(example))
    data["official_example"] = official_score(vf, af)
    for row in rows:
        started = time.monotonic()
        path = ROOT / row["output_path"]
        assert sha(path) == row["output_sha256"], path
        frames = read_video(path)
        visual = visual_evidence(frames, row["trial_id"], out)
        crops = face_crops(frames, boxes[row["avatar_id"]])
        Image.fromarray(cv2.cvtColor(crops[0], cv2.COLOR_BGR2RGB)).save(out / (row["trial_id"]+"-syncnet-crop.png"))
        vf, af = features(model, crops, audio(path))
        np.savez_compressed(out / (row["trial_id"]+"-features.npz"), video=vf.numpy(), audio=af.numpy())
        result = {"trial_id": row["trial_id"], "output_sha256": row["output_sha256"],
                  **visual, **official_score(vf, af), "shift_controls": controls(vf, af),
                  "audit_wall_s": time.monotonic()-started}
        data["trials"].append(result)
        (out / "quality_metrics.partial.json").write_text(json.dumps(data, indent=2)+"\n")
        print(json.dumps({k:v for k,v in result.items() if k not in ["distance_curve", "shift_controls"]}), flush=True)
    ledger.write_text(json.dumps(data, indent=2)+"\n")


if __name__ == "__main__":
    main()
