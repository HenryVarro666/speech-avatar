"""Two hash-bound listening candidates, with no service or video side effects."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random
import re
import subprocess
import time


def assert_gpu_available(process_csv, selected_uuid, own_pid):
    for row in csv.reader(process_csv.splitlines()):
        if not row:
            continue
        if len(row) != 2 or not row[1].strip().isdigit():
            raise ValueError("unrecognized GPU process query")
        if row[0].strip() == selected_uuid and int(row[1]) != own_pid:
            raise RuntimeError(f"external GPU process on selected device: {row[1].strip()}")


def assert_new_outputs(root, audio_ids):
    for ident in audio_ids:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", ident):
            raise ValueError("invalid audio id")
        for suffix in (".wav", ".float32.npy"):
            path = root / (ident + suffix)
            if path.exists():
                raise FileExistsError(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gpu_processes():
    return subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader"],
        text=True,
    ).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--gpu-uuid", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    request_path = root / "tts_request.json"
    request = json.loads(request_path.read_text())
    output = root / "audio"
    output.mkdir(exist_ok=True)
    assert_new_outputs(output, [v["audio_id"] for v in request["voices"]])
    before = gpu_processes()
    assert_gpu_available(before, args.gpu_uuid, os.getpid())
    if os.environ.get("CUDA_VISIBLE_DEVICES") != args.gpu_uuid:
        raise ValueError("CUDA_VISIBLE_DEVICES must select the checked UUID")
    # Heavy imports and all GPU allocation follow the refusal checks.
    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    torch.set_num_threads(4)
    started = time.perf_counter()
    assert_gpu_available(gpu_processes(), args.gpu_uuid, os.getpid())
    model = Qwen3TTSModel.from_pretrained(
        str(root / "model"), device_map="cuda:0", dtype=torch.bfloat16,
        attn_implementation=request["attention"],
    )
    torch.cuda.synchronize()
    load_s = time.perf_counter() - started
    supported = model.get_supported_speakers()
    if not {v["speaker"].lower() for v in request["voices"]}.issubset(
        {speaker.lower() for speaker in supported}
    ):
        raise ValueError("requested voice is not supported by the actual model")
    metadata = {
        "date_utc": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
        "selected_gpu_uuid": args.gpu_uuid, "compute_before": before,
        "request_sha256": digest(request_path), "script_sha256": digest(Path(__file__)),
        "model_manifest_sha256": digest(root / "model_manifest.json"),
        "model_load_s": load_s, "speakers_supported": supported,
        "versions": {name: importlib.metadata.version(name) for name in
                     ["qwen-tts", "torch", "torchaudio", "transformers", "soundfile"]},
        "timing_scope": "load: before from_pretrained to CUDA synchronized; generation: before generate_custom_voice to CUDA synchronized; save excluded",
    }
    with (root / "run_metadata.json").open("x") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
    for voice in request["voices"]:
        record = {**voice, "seed": request["seed"], "request_sha256": digest(request_path),
                  "human_review": "pending", "date_utc": datetime.now(timezone.utc).isoformat()}
        try:
            assert_gpu_available(gpu_processes(), args.gpu_uuid, os.getpid())
            random.seed(request["seed"])
            np.random.seed(request["seed"])
            torch.manual_seed(request["seed"])
            torch.cuda.manual_seed_all(request["seed"])
            torch.cuda.reset_peak_memory_stats()
            start = time.perf_counter()
            with torch.inference_mode():
                wavs, rate = model.generate_custom_voice(
                    text=request["text"], language=request["language"],
                    speaker=voice["speaker"], instruct=request["instruct"],
                    **request["generation"],
                )
            torch.cuda.synchronize()
            record["generation_s"] = time.perf_counter() - start
            audio = np.asarray(wavs[0], dtype=np.float32)
            if audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
                raise ValueError("invalid generated waveform")
            peak = float(np.max(np.abs(audio)))
            if not 0 < peak < 1:
                raise ValueError(f"silent or clipping waveform: peak={peak}")
            raw = output / (voice["audio_id"] + ".float32.npy")
            path = output / (voice["audio_id"] + ".wav")
            with raw.open("xb") as handle:
                np.save(handle, audio, allow_pickle=False)
            with path.open("xb") as handle:
                sf.write(handle, audio, rate, format="WAV", subtype="PCM_16")
            record.update({
                "status": "generated_pending_listening", "path": str(path.relative_to(root)),
                "sha256": digest(path), "raw_path": str(raw.relative_to(root)),
                "raw_sha256": digest(raw), "sample_rate_hz": rate,
                "samples": len(audio), "duration_s": len(audio) / rate, "raw_peak": peak,
                "transform": "float32 model waveform quantized to PCM16 only; no trimming, normalization, resampling or speed change",
                "peak_torch_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
                "peak_torch_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
                "compute_after": gpu_processes(),
            })
            assert_gpu_available(record["compute_after"], args.gpu_uuid, os.getpid())
        except Exception as exc:
            record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            with (root / "tts_attempts.jsonl").open("a") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(json.dumps(record, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
