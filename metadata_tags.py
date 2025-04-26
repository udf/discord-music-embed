import mutagen
import mutagen.flac
import mutagen.mp3
import mutagen.id3
import mutagen.easyid3

from dataclasses import dataclass
from pathlib import Path


@dataclass(kw_only=True)
class Tags:
  artist: str = ''
  title: str = ''
  album: str = ''
  date: str = ''


def read_audio_tags(f: Path):
  concat = lambda l: ', '.join(l)
  m = mutagen.File(f, easy=True)

  tags: Tags = Tags()
  if isinstance(m.tags, mutagen.flac.VCFLACDict):
    tags.artist = concat(m.tags.get('ARTIST', []))
    tags.title = concat(m.tags.get('TITLE', []))
    tags.date = concat(
      m.tags.get('originalyear')
      or m.tags.get('year')
      or m.tags.get('originaldate')
      or m.tags.get('releasedate')
      or m.tags.get('date')
      or []
    )
    tags.album = concat(m.tags.get('album', []))
  elif isinstance(m.tags, mutagen.easyid3.EasyID3):
    tags.artist = concat(m.tags.get('artist', []))
    tags.title = concat(m.tags.get('title', []))
    tags.date = concat(
      m.tags.get('date', [])
      or m.tags.get('originaldate', [])
    )
    tags.album = concat(m.tags.get('album', []))


  tags.title = tags.title or f.stem
  return tags