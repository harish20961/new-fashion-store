from pathlib import Path

from PIL import Image

SOURCE = Path("raw_images")                # original big photos go here
OUTPUT = Path("frontend/images/products")  # compressed photos land here
MAX_WIDTH = 900
QUALITY = 75

OUTPUT.mkdir(parents=True, exist_ok=True)

for path in SOURCE.glob("*"):
    if path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        continue

    img = Image.open(path).convert("RGB")
    if img.width > MAX_WIDTH:
        new_height = int(img.height * MAX_WIDTH / img.width)
        img = img.resize((MAX_WIDTH, new_height))

    out_path = OUTPUT / (path.stem + ".jpg")
    img.save(out_path, "JPEG", quality=QUALITY, optimize=True)
    print(f"{path.name} -> {out_path.name} ({out_path.stat().st_size // 1024} KB)")