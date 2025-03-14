from dataclasses import dataclass

from metadata_service import AudioMetadata

@dataclass(kw_only=True)
class AudioAsVideo(AudioMetadata):
  content_url: str
  cover_url: str
  site_name: str
  theme_color: str

  def get_html(self):
    song_info = f'{self.artist} - {self.title}' if self.artist else self.title
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <meta property="og:site_name" content="{self.site_name}">
  <meta property="og:title" content="{song_info}">
  <meta property="og:description" content="{self.artist}">
  <meta property="og:image" content="{self.cover_url}">
  <meta name="theme-color" content="{self.theme_color}" />
  <meta property="og:type" content="video.other">

  <meta property="og:video" content="{self.content_url}">
  <meta property="og:video:secure_url" content="{self.content_url}">
  <meta property="og:video:type" content="video/mp4">
  <meta property="og:video:width" content="{self.cover_width}">
  <meta property="og:video:height" content="{self.cover_height}">
  <title>{song_info} | {self.site_name}</title>
</head>
<body>
  <h1>{self.site_name}</h1>
  <h2>{song_info}</h2>
  <img src="{self.cover_url}" width="300" height="300" style="object-fit: contain;" />
  <br/>
  <audio controls src="{self.content_url}"></audio>
  <br/>
  <span>
    <a href="{self.content_url}" download>Link</a>
    <span>|</span>
    <a href="{self.content_url}">Download</a>
  </span>
</body>
</html>
    '''