"""Image-file operations for PVG messages."""

from pathlib import Path

from PIL import Image

from constants import LOSSLESS_FORMATS
from pvg_codec import embed_bytes, extract_bytes


def encode_image(input_path: Path, output_path: Path, message: str) -> None:
    if output_path.suffix.lower() not in LOSSLESS_FORMATS:
        raise ValueError("Output must use a lossless image format (PNG, BMP, or TIFF)")
    with Image.open(input_path) as image:
        encoded = embed_bytes(image, message.encode("utf-8"))
    encoded.save(output_path)


def decode_image(input_path: Path) -> str:
    with Image.open(input_path) as image:
        payload = extract_bytes(image)
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("The embedded payload is not valid UTF-8 text") from exc
