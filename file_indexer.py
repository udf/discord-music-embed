import logging

from config import MUSIC_DIR
from metadata_service import ACCEPTED_FILE_EXTS


# set of relative file paths that are valid for processing
# TODO: rescan on SIGUSR1
discovered_files: set[str] = set()

logger = logging.getLogger('indexer')


def _scan_music_dir():
  global discovered_files
  _new_files: set[str] = set() if discovered_files else discovered_files
  logger.info('getting list of music files...')
  for root, dirs, files in MUSIC_DIR.walk():
    dirs.sort()
    relative_root = root.relative_to(MUSIC_DIR)
    for file in files:
      path = relative_root / file
      if path.suffix.lower() not in ACCEPTED_FILE_EXTS:
        continue
      _new_files.add(str(path))
  logger.info(f'found {len(_new_files)} files')
  discovered_files = _new_files


def scan_music_dir():
  try:
    _scan_music_dir()
    return True
  except:
    logger.exception('Error scanning music directory')
  return False