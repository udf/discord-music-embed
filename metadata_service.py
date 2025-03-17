import logging
import asyncio
import concurrent.futures
import hashlib
import multiprocessing
from dataclasses import dataclass
from functools import partial
from io import BytesIO
from multiprocessing.managers import BaseManager
from pathlib import Path, PurePosixPath
from copy import deepcopy

import mutagen
from PIL import Image

import db
from db import CachedAudioMetadata
from config import COVER_DIR, DEFAULT_COVER_PATH, MUSIC_DIR, METADATA_WORKERS
from metadata_tags import Tags, read_audio_tags


ACCEPTED_FILE_EXTS = {'.flac', '.mp3'}
COVER_SIZE = 512

logger = logging.getLogger('meta:main')


def _mp_init():
  global logger
  current_proc = multiprocessing.current_process()
  logger = logging.getLogger(f'meta:{current_proc.name}')


@dataclass
class ResultWrapper[T]:
  _result: T | None = None

  def set(self, value: T):
    self._result = value

  def get(self) -> T | None:
    return self._result


class MpManager(BaseManager):
  pass


@dataclass(kw_only=True)
class Cover:
  filename: str
  width: int
  height: int


@dataclass(kw_only=True)
class AudioMetadata(CachedAudioMetadata):
  cover_width: int = 0
  cover_height: int = 0
  is_complete: bool = False

  @classmethod
  def create_placeholder(cls, path: PurePosixPath):
    return cls(
      path=str(path),
      cover_filename=DEFAULT_COVER.filename,
      cover_width=DEFAULT_COVER.width,
      cover_height=DEFAULT_COVER.height,
      tags=Tags(title=path.stem)
    )


def get_embedded_art(f):
  m = mutagen.File(f)
  pics = []
  if isinstance(m, mutagen.flac.FLAC):
    pics = [p.data for p in m.pictures]
  elif isinstance(m, mutagen.mp3.MP3):
    pics = [m.get(k).data for k in m.keys() if k.startswith('APIC:')]
  else:
    raise NotImplementedError
  return pics


def get_cover_art_image(f, read_tags=True):
  if read_tags:
    covers = get_embedded_art(f)
    if covers:
      return Image.open(BytesIO(covers[0])), None
  # find first image in the same directory
  parent = Path(f).parent
  for image_path in parent.glob('*.*'):
    if image_path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
      return Image.open(image_path), image_path
  return None, None


def read_image_size(path):
  im = Image.open(path)
  return im.size


def resize_and_store_image(im: Image.Image) -> Cover:
  im_hash = hashlib.sha256(im.tobytes()).hexdigest()
  filename = f'{im_hash}.jpg'
  out_path = COVER_DIR / filename

  if out_path.exists():
    width, height = read_image_size(out_path)
    return Cover(filename=filename, width=width, height=height)

  im = im.convert('RGB')
  width, height = im.size
  size_ratio = min(COVER_SIZE/width, COVER_SIZE/height)
  width, height = round(width * size_ratio), round(height * size_ratio)
  im = im.resize((width, height), resample=Image.Resampling.LANCZOS, reducing_gap=2.0)

  im_data = BytesIO()
  im.save(im_data, format='JPEG', quality=95)
  im_data.seek(0)
 
  try:
    with open(out_path, 'xb') as f:
      f.write(im_data.getbuffer())
  except FileExistsError:
    pass
  return Cover(filename=filename, width=width, height=height)


def store_audio_file_metadata(metadata: AudioMetadata):
  metadata = deepcopy(metadata)
  metadata.cover_filename = metadata.cover_filename if metadata.cover_filename != DEFAULT_COVER.filename else ''
  db.store_audio_metadata(metadata)


def _get_audio_metadata(res: ResultWrapper[AudioMetadata], rel_path: PurePosixPath, uuid: str):
  metadata = res.get()
  assert metadata is not None
  metadata.path = str(rel_path)
  cache = db.get_audio_metadata_by_path(rel_path)
  if cache:
    logger.info(f'[{uuid}] loading metadata from cache')
    # load from cache, even if it is potentialy outdated
    metadata.tags = cache.tags
    res.set(metadata)

    if cache.cover_filename:
      try:
        width, height = read_image_size(COVER_DIR / cache.cover_filename)
        metadata.cover_filename = cache.cover_filename
        metadata.cover_width = width
        metadata.cover_height = height
        metadata.is_complete = True
        res.set(metadata)
      except FileNotFoundError:
        logger.warning(f'[{uuid}] cached cover missing!')
      except:
        logger.exception(f'[{uuid}] error reading cached cover!')

  local_path = Path(MUSIC_DIR) / rel_path
  stat = local_path.stat()

  cache_mtime = (cache.mtime or 0) if cache and metadata.is_complete else 0
  cache_is_valid = cache and cache_mtime > stat.st_mtime

  # read and resize cover (only read tags is cache is outdated)
  cover_art_im, cover_art_path = get_cover_art_image(local_path, read_tags=not cache_is_valid)
  # only process cover if it's newer than the cache
  cover_art_mtime = Path(cover_art_path).stat().st_mtime if cover_art_path else 0
  if cover_art_im and cover_art_mtime >= cache_mtime:
    logger.info(f'[{uuid}] updating cover art from {cover_art_path or '<tags>'}')
    cover = resize_and_store_image(cover_art_im)
    metadata.cover_filename = cover.filename
    metadata.cover_width = cover.width
    metadata.cover_height = cover.height
    res.set(metadata)
    store_audio_file_metadata(metadata)

  if cache_is_valid:
    # cache is newer than file, nothing to do
    return

  # read metadata
  logger.info(f'[{uuid}] fetching file metadata')
  metadata.tags = read_audio_tags(local_path)
  metadata.is_complete = True
  res.set(metadata)

  store_audio_file_metadata(metadata)


async def get_audio_metadata(rel_path: PurePosixPath, uuid: str, timeout: float) -> AudioMetadata:
  res: ResultWrapper[AudioMetadata] = manager.ResultWrapper()
  loop = asyncio.get_running_loop()
  res.set(AudioMetadata.create_placeholder(rel_path))
  try:
    fn = partial(_get_audio_metadata, res=res, rel_path=rel_path, uuid=uuid)
    await asyncio.wait_for(loop.run_in_executor(process_pool, fn), timeout=timeout)
  except asyncio.TimeoutError:
    logger.info(f'[{uuid}] timeout={timeout} reached while fetching metadata')
  return res.get()


def init():
  global DEFAULT_COVER, process_pool, manager, busy_files
  COVER_DIR.mkdir(exist_ok=True, parents=True)
  DEFAULT_COVER = resize_and_store_image(Image.open(DEFAULT_COVER_PATH))

  process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=METADATA_WORKERS, initializer=_mp_init, initargs=())

  MpManager.register('ResultWrapper', ResultWrapper)
  MpManager.register('set', set)
  manager = MpManager()
  manager.start()
  busy_files = manager.set()


DEFAULT_COVER: Cover = Cover(filename='', width=0, height=0)

process_pool = None
manager: MpManager = None
