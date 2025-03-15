import os
from pathlib import Path, PurePosixPath

# port to run the server on
PORT = int(os.environ.get('PORT', 36900))
# set to 1 to serve files (for testing)
SERVE_FILES = os.environ.get('SERVE_FILES', '0') == '1'

# size of process pool used for reading file metadata
METADATA_WORKERS = int(os.environ.get('METADATA_WORKERS', 4))

# host to use when generating absolute urls to files
HTTP_HOST = os.environ.get('HTTP_HOST', f'localhost:{PORT}')

# used in templates
SITE_NAME = os.environ.get('SITE_NAME', 'Gaia')
PAGE_TITLE = os.environ.get('PAGE_TITLE', SITE_NAME)
THEME_COLOR = os.environ.get('THEME_COLOR', '#F5A9B8')

# local path of the music directory
MUSIC_DIR = Path(os.environ['MUSIC_DIR']).resolve()
# http path of the music directory
HTTP_ROOT = PurePosixPath(os.environ.get('HTTP_ROOT', '/'))

# local path of the cover directory
COVER_DIR = Path(os.environ.get('COVER_DIR', 'cover/')).resolve()
# http path of the cover directory
COVER_HTTP_ROOT = PurePosixPath(os.environ.get('COVER_HTTP_ROOT', '/cover/'))

DEFAULT_COVER_PATH = Path(os.environ.get('DEFAULT_COVER_PATH', 'default.png')).resolve()