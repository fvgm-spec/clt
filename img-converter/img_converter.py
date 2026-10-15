#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from PIL import Image

SUPPORTED_FORMATS = {"jpg", "jpeg", "webp"}


DEFAULT_SIZE = (1200, 630)


def convert(input_path: Path, fmt: str, output_dir: Path = None, size: tuple = DEFAULT_SIZE) -> Path:
    fmt = fmt.lower().lstrip(".")
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}")

    dest_dir = output_dir or Path.home() / "Pictures/Converted"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{input_path.stem}.{fmt}"

    img = Image.open(input_path).convert("RGB").resize(size)
    save_fmt = "JPEG" if fmt in ("jpg", "jpeg") else fmt.upper()
    img.save(dest, save_fmt)

    if dest.stat().st_size > 2 * 1024 * 1024:
        dest.unlink()
        raise ValueError(f"Converted file exceeds 2 MB limit: {dest.name}")

    return dest


def main():
    parser = argparse.ArgumentParser(description="Convert PNG files to jpg, jpeg, or webp")
    parser.add_argument("files", nargs="+", help="PNG file(s) to convert")
    parser.add_argument("-f", "--format", required=True, choices=SUPPORTED_FORMATS, help="Output format")
    parser.add_argument("-o", "--output-dir", help="Output directory (default: same as input)")
    parser.add_argument("-s", "--size", default="1200x630", help="Output size WxH (default: 1200x630)")
    args = parser.parse_args()

    w, h = map(int, args.size.lower().split("x"))
    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    for f in args.files:
        path = Path(f)
        if not path.exists():
            print(f"[skip] {f} — file not found", file=sys.stderr)
            continue
        try:
            dest = convert(path, args.format, output_dir, (w, h))
            print(f"[ok] {path.name} → {dest}")
        except ValueError as e:
            print(f"[error] {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
