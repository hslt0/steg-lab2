"""Constants used by the grayscale PVG implementation."""

PVG_RANGES = (
    (0, 7, 3),
    (8, 15, 3),
    (16, 31, 4),
    (32, 63, 5),
    (64, 127, 6),
    (128, 255, 7),
)
HEADER_SIZE = 4
MAX_PAYLOAD_SIZE = (1 << (HEADER_SIZE * 8)) - 1
LOSSLESS_FORMATS = {".bmp", ".png", ".tif", ".tiff"}
