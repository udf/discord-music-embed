from dataclasses import dataclass
from pathlib import Path


@dataclass(kw_only=True)
class Tags:
  artist: str = ''
  title: str = ''


def read_audio_tags(f: Path):
  concat = lambda l: ', '.join(l)
  m = mutagen.File(f)

  tags: Tags = Tags()
  if isinstance(m, mutagen.flac.FLAC):
    tags.artist = concat(m.tags.get('ARTIST', []))
    tags.title = concat(m.tags.get('TITLE', []))
  elif isinstance(m, mutagen.mp3.MP3):
    tags.artist = concat(m.tags.get('TPE1', []))
    tags.title = concat(m.tags.get('TIT2', []))

  tags.title = tags.title or f.stem
  return tags