from dataclasses import dataclass

from config import PAGE_TITLE, SITE_NAME, THEME_COLOR
from metadata_service import AudioMetadata

@dataclass(kw_only=True)
class AudioAsVideo(AudioMetadata):
  content_url: str
  cover_url: str

  def get_html(self, gmt_now):
    song_info = f'{self.artist} - {self.title}' if self.artist else self.title
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{song_info}">
  <meta property="og:description" content="{self.artist}">
  <meta property="og:image" content="{self.cover_url}">
  <meta name="theme-color" content="{THEME_COLOR}" />
  <meta property="og:type" content="video.other">

  <meta property="og:video" content="{self.content_url}">
  <meta property="og:video:secure_url" content="{self.content_url}">
  <meta property="og:video:type" content="video/mp4">
  <meta property="og:video:width" content="{self.cover_width}">
  <meta property="og:video:height" content="{self.cover_height}">
  <title>{song_info} | {PAGE_TITLE}</title>
</head>
<body>
  <h1>{PAGE_TITLE}</h1>
  <h2>{song_info}</h2>
  <img src="{self.cover_url}" width="300" height="300" style="object-fit: contain;" />
  <br/>
  <audio controls src="{self.content_url}"></audio>
  <br/>
  <span>
    <a href="{self.content_url}">Link</a>
    <span>|</span>
    <a href="{self.content_url}" download>Download</a>
  </span>
  <hr/>
  <p>Generated at: {gmt_now}</p>
</body>
</html>
    '''