import string
import html
from typing import override
from config import PAGE_TITLE, SITE_NAME, THEME_COLOR
from metadata_service import AudioMetadata
from metadata_tags import Tags


class HTMLFormatter(string.Formatter):
  @override
  def format_field(self, value, format_spec: str):
    is_attr = False
    if format_spec == 'attr':
      format_spec = ''
      is_attr = True
    return html.escape(
      format(value, format_spec),
      quote=is_attr
    )


def get_album_info(tags: Tags):
  match (tags.album, tags.date):
    case album, '':
      return f'{album}'
    case album, date:
      return f'{album or 'Unknown Album'} ({date})'


def get_html(
  meta: AudioMetadata,
  content_url: str,
  cover_url: str,
  gmt_now: str
):
  tags = meta.tags
  song_info = f'{tags.artist} - {tags.title}' if tags.artist else tags.title
  album_info = get_album_info(tags)
  site_name = f'{SITE_NAME} | {album_info}' if album_info else SITE_NAME
  cover_width = meta.cover_width
  cover_height = meta.cover_height

  return FORMATTER.format('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <meta property="og:site_name" content="{site_name:attr}">
  <meta property="og:title" content="{song_info:attr}">
  <meta property="og:description" content="{song_info:attr}">
  <meta property="og:image" content="{cover_url:attr}">
  <meta name="theme-color" content="{THEME_COLOR:attr}" />
  <meta property="og:type" content="video.other">

  <meta property="og:video" content="{content_url:attr}">
  <meta property="og:video:secure_url" content="{content_url:attr}">
  <meta property="og:video:type" content="video/mp4">
  <meta property="og:video:width" content="{cover_width:attr}">
  <meta property="og:video:height" content="{cover_height:attr}">
  <title>{song_info} | {PAGE_TITLE}</title>

  <style>
    body {{ background-color: #181a1b; color: hsl(36, 10%, 95%); }}
    a {{ color: hsl(210, 100%, 60%); }}
    a:visited {{ color: hsl(260, 100%, 60%); }}
    a:hover {{ color: hsl(210, 100%, 80%); }}
    a:visited:hover {{ color: hsl(260, 100%, 80%); }}
    h2 {{ margin-bottom: 0.2em; }}
    h3 {{ color: hsl(36, 10%, 75%); margin-top: 0.2em; }}
    @-moz-document url-prefix() {{
      audio {{ background-color: #606060; }}
    }}
  </style>
</head>
<body>
  <h1>{PAGE_TITLE}</h1>
  <h2>{song_info}</h2>
  <h3>{album_info}</h3>
  <img src="{cover_url:attr}" width="300" height="300" style="object-fit: contain;" />
  <br/>
  <audio controls src="{content_url:attr}"></audio>
  <br/>
  <span>
    <a href="{content_url:attr}">Link</a>
    <span>|</span>
    <a href="{content_url:attr}#download" download>Download</a>
  </span>
  <hr/>
  <p>Generated at: {gmt_now}</p>
</body>
</html>
''',
  THEME_COLOR=THEME_COLOR,
  PAGE_TITLE=PAGE_TITLE,
  site_name=site_name,
  song_info=song_info,
  cover_url=cover_url,
  content_url=content_url,
  cover_width=cover_width,
  cover_height=cover_height,
  album_info=album_info,
  gmt_now=gmt_now,
)


FORMATTER = HTMLFormatter()