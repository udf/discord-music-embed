import asyncio
import concurrent.futures
import logging
from pathlib import PurePosixPath
import uuid

from aiohttp import web
from yarl import URL

from config import (
  PORT, HTTP_HOST, SERVE_FILES,
  SITE_NAME, THEME_COLOR,
  MUSIC_DIR, HTTP_ROOT,
  COVER_DIR, COVER_HTTP_ROOT,
)
import metadata_service
from metadata_service import get_audio_metadata
from templates import AudioAsVideo


ACCEPTED_FILE_EXTS = {'.flac', '.mp3'}

process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=8)

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
  host = req.headers.get('X-FORWARDED-FOR', HTTP_HOST)

  rel_path = PurePosixPath(req.path).relative_to(HTTP_ROOT)
  local_path = MUSIC_DIR / rel_path

  if SERVE_FILES and (res := serve_file(req, local_path)) is not None:
    return res

  if not local_path.is_file() or local_path.suffix.lower() not in ACCEPTED_FILE_EXTS:
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
    content_url=str(URL.build(scheme=req.scheme, authority=host, path=req.path)),
    cover_url=str(URL.build(
      scheme=req.scheme,
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


if __name__ == '__main__':
  metadata_service.init()

  # cache node id
  uuid.getnode()

  app = web.Application(middlewares=[uuid_middleware])
  app.add_routes(routes)

  web.run_app(
    app,
    port=PORT,
    access_log_format='%a %t (%Tfs) [%{X-UUID}o] "%r" %s %b "%{Referer}i" "%{User-Agent}i"'
  )