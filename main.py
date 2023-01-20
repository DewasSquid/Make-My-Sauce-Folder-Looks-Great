import asyncio
import os
from time import sleep

import saucenao_api.errors as saucenao_errors
from exiftool import ExifToolHelper
from PIL import Image
from pygelbooru import Gelbooru
from saucenao_api import SauceNao

import module.main_errors as main_errors
from config import *
from module.json_logs import JsonLogs

sauce = SauceNao(sauce_nao_api_keys)
gelbooru = Gelbooru(gelbooru_api_key, gelbooru_user_id)

# Gelbooru API
async def retrieve_gelbooru_info(post_url):
    """Convert gelbooru URL into a post ID and return the corresponding post as an object."""
    post_id = post_url.split("&")[2]
    post_id = post_id.replace("id=", "")
    post_id = int(post_id)

    return await gelbooru.get_post(post_id)

def check_gelbooru_content(urls):
    """Check if the content is on Gelbooru"""
    return next((url for url in urls if "gelbooru" in url), None)

# Exif data manipulation
def set_exif_keywords(file: str, keywords: list):
    """Change the keywords of the file"""
    with ExifToolHelper() as et:
        et.set_tags(
            file,
            tags={"Keywords": keywords},
            params=["-P", "-overwrite_original"]
        )

def get_exif_keywords(file: str):
        """get the keywords of the file"""
        with ExifToolHelper() as et:
            for d in et.get_tags(file, tags=["Keywords"]):
                return d["IPTC:Keywords"]

# Main part of the code
class Main():
    def __init__(self, file, file_with_path):
        self.file = file
        self.file_with_path = file_with_path
        self.file_name_with_path, self.file_extension = os.path.splitext(self.file_with_path.lower())
        
        if os.stat(self.file_with_path).st_size > UPLOAD_MAX_SIZE:
            raise main_errors.fileSizeExceeded(f"File size exceeds {UPLOAD_MAX_SIZE / 1000000}MB.")
        
        self.main()
    
    def main(self):
        self.results = sauce.from_file(self.file_with_path)
        self.post = self.browse_results()
        
        print("Request limits:", self.results.long_remaining, self.results.short_remaining)

        if self.post is not None:
            self.process_file_edit()
            
            JsonLogs().add(self.file_with_path)
            return
        
        print("No result.")
        JsonLogs().add(self.file_with_path)
    
    def browse_results(self):
        for result in self.results:
            r_url = check_gelbooru_content(result.urls)
            if r_url is not None: return asyncio.run(retrieve_gelbooru_info(r_url))
        return None
    
    def process_file_edit(self):
        if self.file_extension in [".png", ".webp"]:
            print("Converting to *.jpg to provide support for keywords...")
            self.convert_to_jpg()
        
        if self.file_extension in [".jpg", ".jpeg", ".jfif", ".pjpeg", ".pjp", ".tif", ".tiff"]:
            # Exif keywords are only compatible with JPG and TIFF files.
            if len(self.file) > MAX_FILE_NAME_SIZE_BEFORE_RENAMING:
                print("Shortening the file name to avoid error with exiftool...")
                self.shorten_file_name()
                print(f"renamed to {self.file_with_path}")
            
            set_exif_keywords(self.file_with_path, self.post.tags)
            print("File keywords where successfully changed to:", get_exif_keywords(self.file_with_path))
            return
        
        # Change the file name instead of it's keywords
        self.rename_file_to_tags()
        print("File was succesfully renamed to:", self.file_with_path)

    def convert_to_jpg(self):
        im = Image.open(self.file_with_path)
        rgb_im = im.convert('RGB')
        rgb_im.save(f"{self.file_name_with_path}.jpg")
        
        os.remove(self.file_with_path)

        self.file_extension = ".jpg"
        self.file_with_path = self.file_name_with_path + self.file_extension
        self.file = self.file_with_path.split("/")[-1]
    
    def shorten_file_name(self):
        original_stat = os.stat(self.file_with_path)
        
        new_name = self.file[-MAX_FILE_NAME_SIZE_BEFORE_RENAMING::].split(".")[0]
        os.rename(self.file_with_path, f"{FOLDER}\\{new_name}{self.file_extension}")
        
        self.file_name_with_path = f"{FOLDER}\\{new_name}"
        self.file_with_path = self.file_name_with_path + self.file_extension
        self.file = self.file_with_path.split("\\")[-1]
        
        os.utime(self.file_with_path, (original_stat.st_atime, original_stat.st_mtime))  # Conserve creation date and modification date
    
    def rename_file_to_tags(self):
        new_file_name = "_".join(self.post.tags)
        new_file_name = new_file_name[-200::]
        for char in BAD_CHARACTERS:
            new_file_name = new_file_name.replace(char, BAD_CHARACTERS_REPLACEMENT)
        new_file_path = os.path.join(FOLDER, new_file_name)
        
        new_file = new_file_path + self.file_extension
        
        file_num = 0
        while os.path.exists(new_file):
            # Another file already exists with the same name
            file_num += 1
            new_file = f"{new_file_path}_-{file_num}-{self.file_extension}"
        
        os.rename(self.file_with_path, new_file)
        
        self.file = new_file_name + self.file_extension
        self.file_with_path = new_file

def check_file_eligibility(file):
    """Return False if the file cannot be processed. Return True otherwise."""
    if JsonLogs().check(file):
        print("Already Marked. Skipping...")
        return False
    
    if file.lower().endswith((".mp4", ".webm")):
        print("Obselete file type. Skipping...")
        return False

    return True

def _exec_main(file, file_with_path):
    try:
        Main(file, file_with_path)
        
        print("10 seconds timeout..")
        sleep(10)
    except saucenao_errors.ShortLimitReachedError as e:
        print("30 seconds timeout...")
        sleep(30)
        
        _exec_main(file, file_with_path)
    except Exception as e:
        if "post" in str(e):
            print("Failed to get post. Marking...")
            JsonLogs().add(file_with_path)
            
        print("Error:", e)

for file in os.listdir(FOLDER):
    file_with_path = os.path.join(FOLDER, file)
    
    print("Current:", file_with_path)
    if not check_file_eligibility(file_with_path):
        continue
    
    _exec_main(file, file_with_path)