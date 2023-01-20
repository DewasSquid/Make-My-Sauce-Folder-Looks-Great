# API
# https://saucenao.com
sauce_nao_api_keys = "API KEY"  #! Has a request limit : 4 per 30 seconds // 99 per day

# https://gelbooru.com
# None can be used for these variables
gelbooru_api_key = None
gelbooru_user_id = None

# DIRECTORY AND FILE PROCESSING
# The folder containing every images
FOLDER = "./images"
# Maximum size of file upload in bytes ( 1 byte = 1 000 000 MB)
UPLOAD_MAX_SIZE = 2000000

# FILE RENAMING
# List of bad characters that can't be put in a file name
BAD_CHARACTERS = ["/", "?", "%", "&", "*", " ", "|", "=", "!", ":", ";", "(", ")"]
BAD_CHARACTERS_REPLACEMENT = "_"  # Bad characters will be replaced with this character when changing a file name
# If a png or webp file is detected. It will automatically be converted to jpg to provide keyword compatibility.
# If the file name is too long, it will be shortened to avoid problems with exiftool :
MAX_FILE_NAME_SIZE_BEFORE_RENAMING = 30