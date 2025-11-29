import os
import csv
import json
import uuid
import requests
from slugify import slugify
from bs4 import BeautifulSoup
from urllib.parse import urlparse


# ------------------------------------------------
# Helper: Download an image and save with UUID name
# ------------------------------------------------
def download_image(url, save_dir="dataset/images"):
    os.makedirs(save_dir, exist_ok=True)

    try:
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1] or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(save_dir, filename)

        r = requests.get(url, stream=True, timeout=10)
        r.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        return file_path

    except Exception as e:
        print(f"[WARN] Failed to download {url}: {e}")
        return None


# ------------------------------------------------
# Helper: Scrape text + images from a news URL
# (Works for most standard news & fact-check sites)
# ------------------------------------------------
def scrape_article(url):
    print(f"[INFO] Scraping: {url}")

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Extract title
        title = soup.find("title").get_text().strip()

        # Extract text from paragraphs
        paragraphs = [p.get_text().strip() for p in soup.find_all("p")]
        text = " ".join(paragraphs)

        # Extract images
        imgs = []
        for img in soup.find_all("img"):
            if "src" in img.attrs:
                src = img["src"]
                if src.startswith("http"):
                    imgs.append(src)

        return {
            "title": title,
            "text": text,
            "images": imgs
        }

    except Exception as e:
        print(f"[ERROR] Failed to scrape {url}: {e}")
        return None


# ------------------------------------------------
# Build dataset entry from URL + label (real/fake)
# ------------------------------------------------
def build_entry(url, label):
    article = scrape_article(url)
    if not article:
        return None

    downloaded_images = []
    for img_url in article["images"]:
        path = download_image(img_url)
        if path:
            downloaded_images.append(path)

    return {
        "id": uuid.uuid4().hex,
        "title": article["title"],
        "text": article["text"],
        "image_paths": downloaded_images,
        "label": label,
        "source_url": url
    }


# ------------------------------------------------
# Save dataset to JSONL
# ------------------------------------------------
def save_jsonl(entries, filename="dataset/news_dataset.jsonl"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", encoding="utf8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"[✔] Saved JSONL dataset: {filename}")


# ------------------------------------------------
# Save dataset to CSV
# ------------------------------------------------
def save_csv(entries, filename="dataset/news_dataset.csv"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", encoding="utf8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "text", "image_paths", "label", "source_url"])

        for e in entries:
            writer.writerow([
                e["id"],
                e["title"],
                e["text"][:500],   # avoid huge csv cells
                ";".join(e["image_paths"]),
                e["label"],
                e["source_url"]
            ])

    print(f"[✔] Saved CSV dataset: {filename}")


# ------------------------------------------------
# MAIN: Build dataset from URL lists
# ------------------------------------------------
def build_dataset(real_urls, fake_urls):
    dataset = []

    print("\n=== Building REAL NEWS samples ===")
    for url in real_urls:
        entry = build_entry(url, label="real")
        if entry:
            dataset.append(entry)

    print("\n=== Building FAKE NEWS samples ===")
    for url in fake_urls:
        entry = build_entry(url, label="fake")
        if entry:
            dataset.append(entry)

    return dataset


# ------------------------------------------------
# Example Usage
# ------------------------------------------------
if __name__ == "__main__":

    # Provide your own URLs here
    real_news_urls = [
        'https://www.bbc.com/news'
    ]

    fake_news_urls = [
    ]

    dataset = build_dataset(real_news_urls, fake_news_urls)

    # Save
    save_jsonl(dataset)
    save_csv(dataset)
