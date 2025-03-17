from argparse import _VersionAction
import multiprocessing
from pathlib import PurePosixPath
import sqlite3
import logging
from dataclasses import dataclass

from metadata_tags import Tags


logger = logging.getLogger('db')
DB_VERSION = 1
db = sqlite3.connect('cache.db')
db.row_factory = sqlite3.Row


@dataclass(kw_only=True)
class CachedAudioMetadata:
  path: str
  mtime: int | None = None
  cover_filename: str = ''
  tags: Tags


def get_audio_metadata_by_path(relative_path: PurePosixPath):
  with db as cur:
    row: sqlite3.Row = cur.execute(
      '''
        SELECT
          path, mtime, cover_filename, artist, title, album, date
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
    tags=Tags(
      artist=row['artist'],
      title=row['title'],
      album=row['album'],
      date=row['date'],
    )
  )


def store_audio_metadata(meta: CachedAudioMetadata):
  with db as cur:
    _ = cur.execute(
      (
        'INSERT OR REPLACE INTO audio_files'
        '(path, cover_filename, artist, title, album, date)'
        'VALUES'
        '(:path, :cover_filename, :artist, :title, :album, :date)'
      ),
      {
        'path': meta.path,
        'cover_filename': meta.cover_filename,
        'artist': meta.tags.artist,
        'title': meta.tags.title,
        'album': meta.tags.album,
        'date': meta.tags.date,
      }
    )


if multiprocessing.parent_process() is None:
  logger.info(f'Initialising db...')
  with db as cur:
    row: sqlite3.Row = cur.execute('PRAGMA user_version').fetchone()
    version: int = row['user_version']
    if version < DB_VERSION:
      logger.info('old database detected, recreating...')
      _ = cur.execute('DROP TABLE IF EXISTS audio_files')
      _ = cur.execute(f'PRAGMA user_version = {DB_VERSION}')
    _ = cur.execute('''
      CREATE TABLE IF NOT EXISTS audio_files (
        path TEXT PRIMARY KEY NOT NULL,
        mtime INTEGER DEFAULT (unixepoch()) NOT NULL,
        cover_filename TEXT NOT NULL,
        artist TEXT NOT NULL,
        title TEXT NOT NULL,
        album TEXT NOT NULL,
        date TEXT NOT NULL
      )
    ''')
