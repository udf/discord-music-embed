import asyncio
import concurrent.futures
import logging
from pathlib import PurePosixPath
import uuid

from aiohttp import web
from yarl import URL

from config import (
  PORT, HTTP_HOST, SERVE_FILES,
  MUSIC_DIR, HTTP_ROOT,
  COVER_DIR, COVER_HTTP_ROOT,
)
import metadata_service
from metadata_service import get_audio_metadata
from templates import AudioAsVideo


ACCEPTED_FILE_EXTS = {'.flac', '.mp3'}

# set of relative file paths that are valid for processing
# TODO: rescan on SIGUSR1
music_files: set[str] = set()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main')

routes = web.RouteTableDef()


def serve_file(req: web.Request, local_path):
  if req.query_string:
    return
  if local_path.is_file():
    return web.FileResponse(local_path)
  try:
    cover_path = COVER_DIR / PurePosixPath(req.path).relative_to(COVER_HTTP_ROOT)
    return web.FileResponse(cover_path)
  except ValueError:
    pass


@routes.get('/{path:.*}')
async def api_get_root(req: web.Request):
  host = HTTP_HOST or req.headers.get('X-Forwarded-Host', '') or req.host
  scheme = req.headers.get('X-Forwarded-Proto', '') or req.scheme

  rel_path = PurePosixPath(req.path).relative_to(HTTP_ROOT)
  local_path = MUSIC_DIR / rel_path

  if SERVE_FILES and (res := serve_file(req, local_path)) is not None:
    return res

  if str(rel_path) not in music_files:
    return web.Response(
      body=f'400: Path is not a valid file [%UUID%]',
      status=400
    )

  try:
    metadata = await get_audio_metadata(rel_path, uuid=req.get('UUID', '-'), timeout=2)
  except RuntimeError as e:
    return web.Response(body=str(e), status=500)
  except:
    raise

  template = AudioAsVideo(
    **metadata.as_dict(),
    content_url=str(URL.build(scheme=scheme, authority=host, path=req.path)),
    cover_url=str(URL.build(
      scheme=scheme,
      authority=host,
      path=str(COVER_HTTP_ROOT / PurePosixPath(metadata.cover_filename))
    ))
  )

  return web.Response(
    body=template.get_html(),
    content_type='text/html',
    headers={'Cache-Control': 'max-age=600'} if metadata.is_complete else None
  )


@web.middleware
async def uuid_middleware(request: web.Request, handler):
  req_uuid = str(uuid.uuid4())
  request['UUID'] = req_uuid
  resp: web.Response = await handler(request)
  resp.headers['X-UUID'] = req_uuid
  if isinstance(resp, web.Response):
    resp.text = (resp.text or '').replace('%UUID%', req_uuid)
  return resp


def scan_music_dir():
  global music_files
  _music_files = set() if music_files else music_files
  logger.info('walker: getting list of music files...')
  for root, dirs, files in MUSIC_DIR.walk():
    dirs.sort()
    relative_root = root.relative_to(MUSIC_DIR)
    for file in files:
      path = relative_root / file
      if path.suffix.lower() not in ACCEPTED_FILE_EXTS:
        continue
      _music_files.add(str(path))
  logger.info(f'walker: found {len(_music_files)} files')
  music_files = _music_files


async def main():
  app = web.Application(middlewares=[uuid_middleware])
  app.add_routes(routes)

  runner = web.AppRunner(
    app,
    access_log_format='%a %t (%Tfs) [%{X-UUID}o] "%r" %s %b "%{Referer}i" "%{User-Agent}i"',
    handle_signals=True
  )
  await runner.setup()
  site = web.TCPSite(
    runner,
    host='localhost',
    port=PORT
  )
  logger.info('starting web server...')
  await site.start()

  while True:
    try:
      await asyncio.to_thread(scan_music_dir)
    except:
      logger.exception('Error scanning music directory')
    await asyncio.sleep(3600)


if __name__ == '__main__':
  metadata_service.init()

  # cache node id
  uuid.getnode()

  asyncio.run(main())