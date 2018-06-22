"""
Starts subprocess, and interprets its output as controller values.

Inspired by https://github.com/FRC4564/Xbox
"""

import asyncio

from aiohttp import web
from brewblox_service import brewblox_logger, features

LOGGER = brewblox_logger(__name__)
routes = web.RouteTableDef()


DEADZONE = 4000


def get_reader(app: web.Application) -> 'ControllerReader':
    return features.get(app, ControllerReader)


def setup(app: web.Application):
    features.add(app, ControllerReader(app))
    app.router.add_routes(routes)


class ControllerProtocol(asyncio.SubprocessProtocol):
    def __init__(self):
        self._latest: str = None

    @property
    def latest(self):
        return self._latest

    def pipe_data_received(self, fd, data):
        self._latest = data


class ControllerReader(features.ServiceFeature):

    def __init__(self, app: web.Application):
        super().__init__(app)

        self._transport = None
        self._protocol = None
        self._id = None

    @property
    def latest(self):
        if not self._protocol:
            return None

        raw = self._protocol.latest
        return {
            '_id': self._id,
            'left_stick': {
                'x': self._scaled_axis(raw[3:9]),
                'y': self._scaled_axis(raw[13:19]),
                'click': int(raw[90:91]),
            },
            'right_stick': {
                'x': self._scaled_axis(raw[24:30]),
                'y': self._scaled_axis(raw[34:40]),
                'click': int(raw[95:96]),
            },
            'dpad': {
                'up': int(raw[45:46]),
                'down': int(raw[50:51]),
                'left': int(raw[55:56]),
                'right': int(raw[60:61]),
            },
            'back': int(raw[68:69]),
            'guide': int(raw[76:77]),
            'start': int(raw[84:85]),
            'buttons': {
                'a': int(raw[100:101]),
                'b': int(raw[104:105]),
                'x': int(raw[108:109]),
                'y': int(raw[112:113]),
            },
            'left_bumper': int(raw[118:119]),
            'right_bumper': int(raw[123:124]),
            'left_trigger': int(raw[129:132]) / 255.0,
            'right_trigger': int(raw[136:139]) / 255.0
        }

    def _scaled_axis(self, raw, deadzone=DEADZONE):
        raw = int(raw)
        if abs(raw) < deadzone:
            return 0.0
        else:
            if raw < 0:
                return (raw + deadzone) / (32768.0 - deadzone)
            else:
                return (raw - deadzone) / (32767.0 - deadzone)

    async def startup(self, app: web.Application):
        await self.shutdown(app)
        self._id = app['config']['controller_id']
        self._transport, self._protocol = await app.loop.subprocess_exec(
            ControllerProtocol,
            'xboxdrv', '--no-uinput', '--detach-kernel-driver', '--id', str(self._id),
            stdin=None, stderr=None
        )

    async def shutdown(self, app: web.Application):
        if self._transport:
            self._transport.close()
            self._transport = None


@routes.get('/values')
async def object_read(request: web.Request) -> web.Response:
    """
    ---
    summary: Get latest controller values
    tags:
    - Controller
    operationId: game.values
    produces:
    - application/json
    """
    reader = features.get(request.app, ControllerReader)
    return web.json_response(reader.latest)
