"""Download only the official inference checkpoints into this experiment root."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
from huggingface_hub import HfApi, hf_hub_download


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    model_root = root / "models"
    specs = [
        ("TMElyralab/MuseTalk", ["musetalkV15/musetalk.json", "musetalkV15/unet.pth"], ""),
        ("stabilityai/sd-vae-ft-mse", ["config.json", "diffusion_pytorch_model.bin"], "sd-vae"),
        ("openai/whisper-tiny", ["config.json", "pytorch_model.bin", "preprocessor_config.json"], "whisper"),
        ("yzd-v/DWPose", ["dw-ll_ucoco_384.pth"], "dwpose"),
    ]
    records = []
    api = HfApi(token=False)
    for repo, files, folder in specs:
        revision = api.model_info(repo).sha
        for filename in files:
            path = Path(hf_hub_download(repo, filename, revision=revision, token=False,
                                      local_dir=str(model_root / folder)))
            records.append({"repo": repo, "revision": revision, "file": filename,
                            "local_path": str(path.relative_to(root))})
            print(f"downloaded {repo}/{filename}", flush=True)
    extra = [
        ("https://download.pytorch.org/models/resnet18-5c106cde.pth", model_root / "face-parse-bisent/resnet18-5c106cde.pth"),
        ("https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth", model_root / "s3fd/s3fd.pth"),
    ]
    for url, path in extra:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            partial = path.with_suffix(".part")
            urllib.request.urlretrieve(url, partial)
            partial.rename(path)
        records.append({"url": url, "local_path": str(path.relative_to(root))})
    face_path = model_root / "face-parse-bisent/79999_iter.pth"
    if not face_path.exists():
        subprocess.run([str(root / ".venv/bin/gdown"), "154JgKpzCPW82qINcVieuPH3fZ2e0P812", "-O", str(face_path)], check=True)
    records.append({"source": "official MuseTalk download_weights.sh Google Drive id", "local_path": str(face_path.relative_to(root))})
    for row in records:
        path = root / row["local_path"]
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        row.update(sha256=h.hexdigest(), bytes=path.stat().st_size)
    (root / "model_manifest.json").write_text(json.dumps({"models": records}, indent=2) + "\n")
    source = root / "vendor/MuseTalk"
    link = source / "models"
    if not link.exists():
        link.symlink_to(model_root, target_is_directory=True)
    s3fd_link = source / "musetalk/utils/face_detection/detection/sfd/s3fd.pth"
    if not s3fd_link.exists():
        s3fd_link.symlink_to(model_root / "s3fd/s3fd.pth")


if __name__ == "__main__":
    main()
