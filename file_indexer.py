import asyncio
import logging
from pathlib import Path, PurePosixPath
import threading

from config import MUSIC_DIR
from metadata_service import ACCEPTED_FILE_EXTS


# set of relative file paths that are valid for processing
discovered_files: set[str] = set()

scan_lock = threading.Lock()
logger = logging.getLogger('indexer')


def path_is_valid(relative_path: PurePosixPath):
  return str(relative_path) in discovered_files


def path_has_valid_extension(local_path: Path):
  return local_path.suffix.lower() in ACCEPTED_FILE_EXTS


def _scan_music_dir():
  with scan_lock:
    global discovered_files
    _new_files: set[str] = set() if discovered_files else discovered_files
    logger.info('rescanning music files...')
    for root, dirs, files in MUSIC_DIR.walk():
      dirs.sort()
      relative_root = root.relative_to(MUSIC_DIR)
      for file in files:
        path = relative_root / file
        if not path_has_valid_extension(path):
          continue
        _new_files.add(str(path))
    logger.info(f'found {len(_new_files)} files')
    discovered_files = _new_files


def _rescan_if_index_is_outdated(local_path: Path):
  if not path_has_valid_extension(local_path):
    return
  relative_path = local_path.relative_to(MUSIC_DIR)
  is_indexed = str(relative_path) in discovered_files
  is_file = local_path.is_file()
  if (is_indexed and is_file) or (not is_indexed and not is_file):
    return
  discovered_files.add(str(relative_path))
  if scan_lock.locked():
    logger.info('need to rescan but a scan is already in progress, skipping')
    return
  _scan_music_dir()


async def rescan_if_index_is_outdated(local_path: Path):
  await asyncio.to_thread(_rescan_if_index_is_outdated, local_path)


async def scan_music_dir():
  try:
    await asyncio.to_thread(_scan_music_dir)
    return True
  except:
    logger.exception('Error scanning music directory')
  return False