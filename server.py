import asyncio
import datetime
import logging
logging.basicConfig(level=logging.INFO)
import uuid
from pathlib import Path, PurePosixPath

from aiohttp import web
from aiohttp.typedefs import Handler
from yarl import URL

import file_indexer
import metadata_service
import templates
from config import (
  COVER_DIR, COVER_HTTP_ROOT, HTTP_HOST, HTTP_ROOT, MUSIC_DIR, PORT, SERVE_FILES,
)
from metadata_service import get_audio_metadata


logger = logging.getLogger('main')

routes = web.RouteTableDef()


def serve_file(req: web.Request, local_path: Path):
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

  if not file_indexer.path_is_valid(rel_path):
    asyncio.create_task(file_indexer.rescan_if_index_is_outdated(local_path))
    return web.Response(
      body=f'400: Path is not a valid file [%UUID%]',
      status=400
    )

  try:
    metadata = await get_audio_metadata(rel_path, uuid=req.get('UUID', '-'), timeout=2)
  except FileNotFoundError:
    logger.exception(f'Error parsing request {req.get('UUID', '-')}')
    return web.Response(body='404: Path was not found, check logs [%UUID%]', status=404)
  except:
    logger.exception(f'Error parsing request {req.get('UUID', '-')}')
    return web.Response(body='500: Unexpected error occured, check logs [%UUID%]', status=500)

  gmt_now = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
  body = templates.get_html(
    meta=metadata,
    content_url=str(URL.build(scheme=scheme, authority=host, path=req.path)),
    cover_url=str(URL.build(
      scheme=scheme,
      authority=host,
      path=str(COVER_HTTP_ROOT / PurePosixPath(metadata.cover_filename))
    )),
    gmt_now=gmt_now
  )

  return web.Response(
    body=body,
    content_type='text/html',
    headers={
      'Cache-Control': 'public' if metadata.is_complete else 'max-age=5',
      'Last-Modified': gmt_now
    }
  )


@web.middleware
async def uuid_middleware(request: web.Request, handler: Handler):
  req_uuid = str(uuid.uuid4())
  request['UUID'] = req_uuid
  resp = await handler(request)
  resp.headers['X-UUID'] = req_uuid
  if isinstance(resp, web.Response):
    resp.text = (resp.text or '').replace('%UUID%', req_uuid)
  return resp


async def main():
  app = web.Application(middlewares=[uuid_middleware])
  app.add_routes(routes)

  runner = web.AppRunner(
    app,
    access_log_format='%a (%{X-Forwarded-For}i) %t (%Tfs) [%{X-UUID}o] "%r" %s %b "%{Referer}i" "%{User-Agent}i"',
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
  if not await file_indexer.scan_music_dir():
    logger.error('Scanning music directory failed, exiting')
    exit(1)

  while True:
    await asyncio.sleep(3600)


if __name__ == '__main__':
  metadata_service.init()

  # cache node id
  uuid.getnode()

  asyncio.run(main())