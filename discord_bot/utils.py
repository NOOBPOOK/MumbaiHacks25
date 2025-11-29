import hashlib
from urllib.parse import urlparse
import imagehash
from PIL import Image
import requests
import os
import uuid
import os


# -------------------------------------
# TEXT HASHING (normal hashing - SHA256)
# -------------------------------------
def hash_text_sha256(text: str) -> str:
    text = text.lower().strip()
    """Returns SHA-256 hex hash for a sentence."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# -------------------------------------
# IMAGE HASHING (pHash)
# -------------------------------------
def hash_images_phash(image_paths: list[str]) -> list[str]:
    """Returns perceptual pHash (hex) for each image."""
    hashes = []
    for path in image_paths:
        img_hash = imagehash.phash(Image.open(path))
        hashes.append(str(img_hash))   # convert to hex string
    return sorted(hashes)  # keep stable ordering


# -------------------------------------
# COMBINED HASH
# -------------------------------------
def combined_hash(text: str, image_paths: list[str]) -> str:
    t_hash = hash_text_sha256(text)
    i_hashes = hash_images_phash(image_paths)
    return t_hash + "_" + "_".join(i_hashes)


def insert_data(data, supabase):

    result = supabase.table("Messages_Primary").insert(data).execute()
    return result


# Downloads the images to a folder
def download_image(url: str, save_dir: str = r"C:\GithubRepos\MumbaiHacks25\discord_bot\downloads") -> str:
    """
    Downloads an image from a CDN/URL, saves with a unique random name,
    and returns the absolute path to the saved image.
    """
    os.makedirs(save_dir, exist_ok=True)

    # Extract file extension
    parsed = urlparse(url)
    filename_from_url = os.path.basename(parsed.path)

    # Default extension if URL has no extension
    if "." in filename_from_url:
        ext = os.path.splitext(filename_from_url)[1]
    else:
        ext = ".jpg"

    # Generate unique filename
    random_name = f"{uuid.uuid4().hex}{ext}"

    file_path = os.path.join(save_dir, random_name)

    # Download
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(file_path, "wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)

    return os.path.abspath(file_path)


if __name__ == '__main__':

    # # testing here
    # t1 = 'Hello, this is Vedant'
    # t2 = 'Hello, this is Vedant'

    # im1 = [r'C:\GithubRepos\MumbaiHacks25\NewImages\download (1).jpeg', r'C:\GithubRepos\MumbaiHacks25\NewImages\download (2).jpeg']
    # im2 = [r'C:\GithubRepos\MumbaiHacks25\NewImages\download (1).jpeg', r'C:\GithubRepos\MumbaiHacks25\NewImages\download (2).jpeg']

    # c1 = combined_hash(t1, im1)
    # c2 = combined_hash(t2, im2)

    # print(c1, c2)

    # if c1 == c2:
    #     print("Same")
    # else:
    #     print("different")

    url = 'https://cdn.discordapp.com/attachments/1443832839161516072/1443845722767097906/image.png?ex=692a8d9d&is=69293c1d&hm=bb6c5a0de41a628c5dfd5f6601166a84aecc8e34524a1c53c6528e3a44b8a398&'

    download_image(url)