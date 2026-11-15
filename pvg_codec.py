"""PVG encoding and decoding for grayscale pixel data."""

from __future__ import annotations

from collections.abc import Iterator

from PIL import Image

from constants import HEADER_SIZE, MAX_PAYLOAD_SIZE, PVG_RANGES


def _range_for_difference(difference: int) -> tuple[int, int, int]:
    for lower, upper, bit_count in PVG_RANGES:
        if lower <= difference <= upper:
            return lower, upper, bit_count
    raise ValueError(f"Pixel difference is outside 0..255: {difference}")


def _embed_pair(first: int, second: int, secret_value: int) -> tuple[int, int]:
    difference = abs(second - first)
    lower, _, bit_count = _range_for_difference(difference)
    if not 0 <= secret_value < (1 << bit_count):
        raise ValueError(f"Secret value must fit in {bit_count} bits")

    adjustment = lower + secret_value - difference
    delta_first = abs(adjustment) // 2
    delta_second = (abs(adjustment) + 1) // 2

    if second >= first:
        if adjustment > 0:
            first_new = first - delta_first
            second_new = second + delta_second
        else:
            first_new = first + delta_first
            second_new = second - delta_second
    elif adjustment > 0:
        first_new = first + delta_first
        second_new = second - delta_second
    else:
        first_new = first - delta_first
        second_new = second + delta_second

    overflow_first = (
        first_new if first_new < 0 else first_new - 255 if first_new > 255 else 0
    )
    overflow_second = (
        second_new
        if second_new < 0
        else second_new - 255
        if second_new > 255
        else 0
    )
    first_new = max(0, min(255, first_new - overflow_second))
    second_new = max(0, min(255, second_new - overflow_first))
    return first_new, second_new


def _pair_capacity(pixels: list[int]) -> int:
    capacity = 0
    for index in range(0, len(pixels) - 1, 2):
        difference = abs(pixels[index + 1] - pixels[index])
        capacity += _range_for_difference(difference)[2]
    return capacity


def _read_bits(data: bytes, bit_offset: int, bit_count: int) -> tuple[int, int]:
    value = 0
    available = min(bit_count, len(data) * 8 - bit_offset)
    for position in range(bit_offset, bit_offset + available):
        value = (value << 1) | (
            (data[position // 8] >> (7 - position % 8)) & 1
        )
    return value << (bit_count - available), bit_offset + available


def _extract_bits(pixels: list[int]) -> Iterator[int]:
    for index in range(0, len(pixels) - 1, 2):
        difference = abs(pixels[index + 1] - pixels[index])
        lower, _, bit_count = _range_for_difference(difference)
        value = difference - lower
        for shift in range(bit_count - 1, -1, -1):
            yield (value >> shift) & 1


def _read_integer(bits: Iterator[int], bit_count: int) -> int:
    value = 0
    try:
        for _ in range(bit_count):
            value = (value << 1) | next(bits)
    except StopIteration as exc:
        raise ValueError("The image does not contain a complete PVG message") from exc
    return value


def embed_bytes(image: Image.Image, payload: bytes) -> Image.Image:
    """Return a grayscale copy containing payload bytes and a 4-byte length header."""
    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ValueError("Payload is too large for the 4-byte PVG length header")

    output = image.convert("L")
    pixels = list(output.tobytes())
    encoded = len(payload).to_bytes(HEADER_SIZE, "big") + payload
    required_bits = len(encoded) * 8
    capacity = _pair_capacity(pixels)
    if required_bits > capacity:
        raise ValueError(
            f"Message needs {required_bits} bits, but this image holds {capacity} bits"
        )

    bit_offset = 0
    for index in range(0, len(pixels) - 1, 2):
        if bit_offset >= required_bits:
            break
        difference = abs(pixels[index + 1] - pixels[index])
        bit_count = _range_for_difference(difference)[2]
        secret_value, bit_offset = _read_bits(encoded, bit_offset, bit_count)
        pixels[index], pixels[index + 1] = _embed_pair(
            pixels[index], pixels[index + 1], secret_value
        )

    output.putdata(pixels)
    return output


def extract_bytes(image: Image.Image) -> bytes:
    """Extract the byte payload from a grayscale PVG image."""
    pixels = list(image.convert("L").tobytes())
    bits = _extract_bits(pixels)
    payload_length = _read_integer(bits, HEADER_SIZE * 8)
    available_bits = _pair_capacity(pixels)
    required_bits = (HEADER_SIZE + payload_length) * 8
    if required_bits > available_bits:
        raise ValueError("The image header declares a truncated or invalid PVG message")

    return bytes(_read_integer(bits, 8) for _ in range(payload_length))
