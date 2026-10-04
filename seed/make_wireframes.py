"""Generate lo-fi wireframes used as Jira attachments.  python -m seed.make_wireframes
(Pre-generated PNGs are already in assets/; re-run only if you change them.)"""
from PIL import Image, ImageDraw, ImageFont

from common.atlassian import ROOT

INK, MID, LIGHT, PAPER, NOTE = "#2b2b2b", "#8a8a8a", "#e6e6e6", "#ffffff", "#fff4c2"


def font(size, bold=False):
    names = ["DejaVuSans-Bold.ttf", "arialbd.ttf"] if bold else ["DejaVuSans.ttf", "arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def window(title):
    img = Image.new("RGB", (1000, 680), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 980, 660], outline=INK, width=2)
    d.rectangle([20, 20, 980, 60], fill=LIGHT, outline=INK, width=2)
    d.text((36, 30), title, font=font(18, True), fill=INK)
    return img, d


def checkbox(d, x, y, label, checked):
    d.rectangle([x, y, x + 20, y + 20], outline=INK, width=2)
    if checked:
        d.line([x + 4, y + 10, x + 9, y + 16, x + 17, y + 4], fill=INK, width=3)
    d.text((x + 32, y), label, font=font(17), fill=INK)


def radio(d, x, y, label, on):
    d.ellipse([x, y, x + 20, y + 20], outline=INK, width=2)
    if on:
        d.ellipse([x + 6, y + 6, x + 14, y + 14], fill=INK)
    d.text((x + 32, y), label, font=font(17), fill=INK)


def button(d, x, y, w, label, primary=False):
    d.rounded_rectangle([x, y, x + w, y + 42], radius=6, fill=INK if primary else PAPER, outline=INK, width=2)
    tw = d.textlength(label, font=font(17, True))
    d.text((x + (w - tw) / 2, y + 11), label, font=font(17, True), fill=PAPER if primary else INK)


def note(d, x, y, w, lines):
    d.rectangle([x, y, x + w, y + 24 * len(lines) + 16], fill=NOTE, outline=MID)
    for i, line in enumerate(lines):
        d.text((x + 10, y + 8 + 24 * i), line, font=font(15), fill=INK)


def import_wizard():
    img, d = window("Photo Sorting App  |  Import photos (step 2 of 4)")
    d.text((50, 85), "Import options", font=font(24, True), fill=INK)

    d.text((50, 140), "Library location", font=font(17, True), fill=INK)
    d.rectangle([50, 168, 640, 206], outline=INK, width=2)
    d.text((62, 178), r"C:\Users\Family\PhotoLibrary", font=font(17), fill=INK)
    button(d, 660, 166, 120, "Change")

    d.text((50, 236), "How should photos be organized?", font=font(17, True), fill=INK)
    radio(d, 50, 268, "By date (Year / Month folders)", True)
    radio(d, 50, 300, "Keep the original folder structure", False)

    d.text((50, 350), "Filters", font=font(17, True), fill=INK)
    checkbox(d, 50, 382, "Skip screenshots", True)
    checkbox(d, 50, 414, "Detect duplicates (flag only, nothing is deleted)", True)
    checkbox(d, 50, 446, "Skip images smaller than 100 KB", False)

    d.text((50, 500), "Sources: 3 folders, 10,234 images found", font=font(16), fill=MID)
    note(d, 560, 380, 390, ["Originals are copied, never moved.",
                            "Duplicates are only flagged here;",
                            "review happens later."])
    button(d, 640, 590, 140, "Back")
    button(d, 800, 590, 160, "Start import", primary=True)
    d.text((36, 632), "Wireframe v0.2", font=font(13), fill=MID)
    return img


def face_labeling():
    img, d = window("Photo Sorting App  |  People")
    d.text((50, 85), "Who is this?", font=font(26, True), fill=INK)
    d.text((50, 124), "Group 3 of 42  -  appears in 86 photos", font=font(16), fill=MID)

    for i in range(6):  # 6 sample faces
        x, y = 50 + (i % 3) * 150, 165 + (i // 3) * 150
        d.rectangle([x, y, x + 130, y + 130], fill=LIGHT, outline=MID)
        d.ellipse([x + 35, y + 22, x + 95, y + 82], outline=INK, width=2)
        d.arc([x + 15, y + 85, x + 115, y + 160], 200, 340, fill=INK, width=2)

    d.text((50, 480), "Name", font=font(17, True), fill=INK)
    d.rectangle([50, 506, 470, 546], outline=INK, width=2)
    d.text((62, 516), "Type a name or pick someone...", font=font(16), fill=MID)
    button(d, 50, 570, 130, "Save name", primary=True)
    button(d, 192, 570, 140, "Unknown")
    button(d, 344, 570, 126, "Skip for now")

    d.rectangle([540, 165, 950, 546], outline=INK, width=2)
    d.text((560, 180), "Your people (4 of 15)", font=font(18, True), fill=INK)
    for i, name in enumerate(["Dad", "Mom", "Son", "Grandma"]):
        y = 222 + i * 52
        d.ellipse([560, y, 596, y + 36], fill=LIGHT, outline=MID)
        d.text((612, y + 7), name, font=font(17), fill=INK)
    d.text((560, 446), "+ Add a person", font=font(17, True), fill=INK)
    note(d, 540, 566, 410, ["Faces not named go to 'Unknown'",
                            "and are left out of searches."])
    d.text((36, 632), "Mockup v0.1", font=font(13), fill=MID)
    return img


if __name__ == "__main__":
    (ROOT / "assets").mkdir(exist_ok=True)
    import_wizard().save(ROOT / "assets" / "import_wizard_wireframe.png")
    face_labeling().save(ROOT / "assets" / "face_labeling_mockup.png")
    print("Saved wireframes to assets/")
