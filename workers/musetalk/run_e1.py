"""Instrument pinned upstream offline inference without changing its generation code.

One process loads models once. Task wall time excludes shared model loading, includes
preprocessing/merge/encoding, and records first saved composited frame. No streaming claim.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    plan = json.loads((root / "trial_plan.json").read_text())
    source = root / "vendor/MuseTalk"
    result = root / "outputs/e1"
    result.mkdir(parents=True, exist_ok=True)
    ledger = root / "trials.jsonl"
    if ledger.exists():
        raise SystemExit("Refusing to overwrite an existing trial ledger. Use a new run directory.")
    for row in plan["trials"]:
        if digest(root / row["audio_path"]) != row["audio_sha256"]:
            raise ValueError(f"audio hash mismatch: {row['trial_id']}")
        if digest(root / row["video_path"]) != row["video_sha256"]:
            raise ValueError(f"avatar hash mismatch: {row['trial_id']}")
    config = {r["trial_id"]: {"video_path": str(root / r["video_path"]),
                             "audio_path": str(root / r["audio_path"]),
                             "result_name": r["trial_id"] + ".mp4"} for r in plan["trials"]}
    config_path = root / "inference.json"
    config_path.write_text(json.dumps(config, indent=2))
    sys.path[:0] = [str(source), str(source / "musetalk/utils")]
    os.chdir(source)
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")
    import torch
    torch.set_num_threads(4)
    process_started = time.perf_counter()
    import scripts.inference as upstream
    import cv2
    bootstrap = {"import_and_global_model_init_s": time.perf_counter() - process_started,
                 "torch": torch.__version__, "cuda": torch.version.cuda,
                 "device": torch.cuda.get_device_name(0), "source_revision": plan["upstream_revision"],
                 "trial_plan_sha256": digest(root / "trial_plan.json"), "pid": os.getpid(),
                 "created_at_utc": datetime.now(timezone.utc).isoformat(),
                 "timing_definition": "task starts after shared model load; first frame = first saved composited PNG, not presentation"}
    current = {}
    original_load = upstream.load_all_model

    def timed_load(*positional, **keywords):
        start = time.perf_counter()
        models = original_load(*positional, **keywords)
        torch.cuda.synchronize()
        bootstrap["load_all_model_s"] = time.perf_counter() - start
        return models

    upstream.load_all_model = timed_load
    original_landmarks = upstream.get_landmark_and_bbox

    def timed_landmarks(*positional, **keywords):
        start = time.perf_counter()
        value = original_landmarks(*positional, **keywords)
        torch.cuda.synchronize()
        current["landmarks_s"] = time.perf_counter() - start
        return value

    upstream.get_landmark_and_bbox = timed_landmarks
    original_write = cv2.imwrite

    def observed_write(filename, *positional, **keywords):
        success = original_write(filename, *positional, **keywords)
        if success and current and str(filename).startswith(str(result)):
            if current["first_saved_frame_s"] is None:
                current["first_saved_frame_s"] = time.perf_counter() - current["start"]
            current["saved_frames"] += 1
        return success

    cv2.imwrite = observed_write
    original_config_load = upstream.OmegaConf.load

    class TaskMap(dict):
        def __iter__(self):
            for trial in plan["trials"]:
                # Do not begin another trial if an external workload shares this GPU.
                gpu_uuid = subprocess.check_output(["nvidia-smi", "--query-gpu=uuid", "--format=csv,noheader"], text=True).splitlines()[0].strip()
                apps = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader"], text=True)
                external = [line for line in apps.splitlines() if line.split(",")[0].strip() == gpu_uuid and int(line.split(",")[1]) != os.getpid()]
                if external:
                    raise RuntimeError("External GPU process detected; stopping this worker without touching it.")
                current.clear()
                current.update(start=time.perf_counter(), first_saved_frame_s=None, saved_frames=0, landmarks_s=None)
                torch.cuda.reset_peak_memory_stats()
                print("E1_TASK_START", trial["trial_id"], flush=True)
                yield trial["trial_id"]
                torch.cuda.synchronize()
                output = result / "v15" / (trial["trial_id"] + ".mp4")
                capture = cv2.VideoCapture(str(output))
                decodable, frame = capture.read()
                frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = capture.get(cv2.CAP_PROP_FPS)
                capture.release()
                wall = time.perf_counter() - current["start"]
                row = {**trial, "status": "rendered_pending_review" if decodable else "render_failed",
                       "wall_s": wall, "first_saved_frame_s": current["first_saved_frame_s"],
                       "landmarks_s": current["landmarks_s"], "saved_frames": current["saved_frames"],
                       "frame_count": frames, "fps": fps, "rtf": wall / trial["expected_audio_duration_s"],
                       "peak_torch_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
                       "peak_torch_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
                       "output_path": str(output.relative_to(root)),
                       "output_sha256": digest(output) if output.exists() else None,
                       "visual_acceptability": None}
                with ledger.open("a") as stream:
                    stream.write(json.dumps(row) + "\n")
                print("E1_TASK_END", trial["trial_id"], row["status"], round(wall, 3), flush=True)
                if not decodable:
                    raise RuntimeError("Smoke/render failed; preserving failure and stopping before remaining pairs.")

    def load_config(path):
        if Path(path).resolve() == config_path:
            return TaskMap(config)
        return original_config_load(path)

    upstream.OmegaConf.load = load_config
    options = SimpleNamespace(ffmpeg_path=str(root / "bin"), gpu_id=0, vae_type="sd-vae",
                              unet_config="models/musetalkV15/musetalk.json", unet_model_path="models/musetalkV15/unet.pth",
                              whisper_dir="models/whisper", inference_config=str(config_path), bbox_shift=0,
                              result_dir=str(result), extra_margin=10, fps=25,
                              audio_padding_length_left=2, audio_padding_length_right=2, batch_size=8,
                              output_vid_name=None, use_saved_coord=False, saved_coord=False,
                              use_float16=True, parsing_mode="jaw", left_cheek_width=90, right_cheek_width=90, version="v15")
    try:
        upstream.main(options)
    finally:
        bootstrap["process_wall_s"] = time.perf_counter() - process_started
        (root / "run_metadata.json").write_text(json.dumps(bootstrap, indent=2) + "\n")


if __name__ == "__main__":
    main()
