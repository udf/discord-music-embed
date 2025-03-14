import sqlite3
import logging

logger = logging.getLogger('db')
db = sqlite3.connect('cache.db')
db.row_factory = sqlite3.Row

logger.info(f'Initialising db...')
with db as cur:
  cur.execute('''
    CREATE TABLE IF NOT EXISTS audio_files (
      path TEXT PRIMARY KEY NOT NULL,
      mtime INTEGER DEFAULT (unixepoch()) NOT NULL,
      cover_filename TEXT NOT NULL,
      artist TEXT NOT NULL,
      title TEXT NOT NULL
    )
  ''')

def get_audio_file_by_path(path):
  with db as cur:
    return cur.execute('SELECT * FROM audio_files WHERE path = ?', (str(path),)).fetchone()

def set_audio_file_cache(*, path, cover_filename, artist, title):
  with db as cur:
    cur.execute(
      (
        'INSERT OR REPLACE INTO audio_files'
        '(path, cover_filename, artist, title)'
        'VALUES'
        '(:path, :cover_filename, :artist, :title)'
      ),
      {
        'path': str(path),
        'cover_filename': cover_filename,
        'artist': artist,
        'title': title
      }
    )