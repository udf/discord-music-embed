from dataclasses import dataclass
from pathlib import Path


@dataclass(kw_only=True)
class Tags:
  artist: str = ''
  title: str = ''


def read_audio_tags(f: Path):
  concat = lambda l: ', '.join(l)
  m = mutagen.File(f)

  artist = ''
  title = ''
  if isinstance(m, mutagen.flac.FLAC):
    artist = concat(m.tags.get('ARTIST', []))
    title = concat(m.tags.get('TITLE', []))
  elif isinstance(m, mutagen.mp3.MP3):
    artist = concat(m.tags.get('TPE1', []))
    title = concat(m.tags.get('TIT2', []))

  return Tags(
    artist=artist or '',
    title=title or f.stem
  )