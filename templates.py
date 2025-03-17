from config import PAGE_TITLE, SITE_NAME, THEME_COLOR
from metadata_service import AudioMetadata
from metadata_tags import Tags


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

  return f'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <meta property="og:site_name" content="{site_name}">
  <meta property="og:title" content="{song_info}">
  <meta property="og:description" content="{song_info}">
  <meta property="og:image" content="{cover_url}">
  <meta name="theme-color" content="{THEME_COLOR}" />
  <meta property="og:type" content="video.other">

  <meta property="og:video" content="{content_url}">
  <meta property="og:video:secure_url" content="{content_url}">
  <meta property="og:video:type" content="video/mp4">
  <meta property="og:video:width" content="{meta.cover_width}">
  <meta property="og:video:height" content="{meta.cover_height}">
  <title>{song_info} | {PAGE_TITLE}</title>
</head>
<body>
  <h1>{PAGE_TITLE}</h1>
  <h2>{song_info}</h2>
  <h3>{album_info}</h3>
  <img src="{cover_url}" width="300" height="300" style="object-fit: contain;" />
  <br/>
  <audio controls src="{content_url}"></audio>
  <br/>
  <span>
    <a href="{content_url}">Link</a>
    <span>|</span>
    <a href="{content_url}" download>Download</a>
  </span>
  <hr/>
  <p>Generated at: {gmt_now}</p>
</body>
</html>
'''