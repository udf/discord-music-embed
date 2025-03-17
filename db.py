import multiprocessing
from pathlib import PurePosixPath
import sqlite3
import logging
from dataclasses import dataclass


logger = logging.getLogger('db')
db = sqlite3.connect('cache.db')
db.row_factory = sqlite3.Row


@dataclass(kw_only=True)
class CachedAudioMetadata:
  path: str
  mtime: int | None = None
  cover_filename: str
  artist: str
  title: str


def get_audio_metadata_by_path(relative_path: PurePosixPath):
  with db as cur:
    row = cur.execute(
      '''
        SELECT
          path, mtime, cover_filename, artist, title
        FROM audio_files
        WHERE path = ?
      ''',
      (str(relative_path),)
    ).fetchone()
  if not row:
    return
  return CachedAudioMetadata(
    path=row['path'],
    mtime=row['mtime'],
    cover_filename=row['cover_filename'],
    artist=row['artist'],
    title=row['title'],
  )


def store_audio_metadata(meta: CachedAudioMetadata):
  with db as cur:
    _ = cur.execute(
      (
        'INSERT OR REPLACE INTO audio_files'
        '(path, cover_filename, artist, title)'
        'VALUES'
        '(:path, :cover_filename, :artist, :title)'
      ),
      {
        'path': meta.path,
        'cover_filename': meta.cover_filename,
        'artist': meta.artist,
        'title': meta.title
      }
    )


if multiprocessing.parent_process() is None:
  logger.info(f'Initialising db...')
  with db as cur:
    _ = cur.execute('''
      CREATE TABLE IF NOT EXISTS audio_files (
        path TEXT PRIMARY KEY NOT NULL,
        mtime INTEGER DEFAULT (unixepoch()) NOT NULL,
        cover_filename TEXT NOT NULL,
        artist TEXT NOT NULL,
        title TEXT NOT NULL
      )
    ''')