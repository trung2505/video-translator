from PIL import Image
from typing import Tuple


def validate_image(path: str) -> Tuple[int, int]:
    """Open image and return (width, height). Raises on invalid images."""
    with Image.open(path) as im:
        im.verify()
        return im.width, im.height


def resize_image(path: str, out_path: str, max_size: Tuple[int, int] = (2048, 2048)) -> None:
    with Image.open(path) as im:
        im.thumbnail(max_size)
        im.save(out_path)
