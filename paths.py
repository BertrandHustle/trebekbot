# used to define absolute paths for use in all modules
from os import path
ROOT_DIR = path.dirname(path.abspath(__file__))
WORDS = path.join(ROOT_DIR, 'support_files', 'words.txt')