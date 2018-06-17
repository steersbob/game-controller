"""
Example of how to import and use the brewblox service
"""

from aiohttp import web
from brewblox_service import brewblox_logger, events, service

from game_controller import reader

routes = web.RouteTableDef()
LOGGER = brewblox_logger(__name__)


def create_parser(default_name='game'):
    parser = service.create_parser(default_name=default_name)
    parser.add_argument('--broadcast-interval',
                        help='Interval (in seconds) between broadcasts of controller state. [%(default)s]',
                        type=float,
                        default=0.1)
    return parser


def main():
    app = service.create_app(parser=create_parser())

    events.setup(app)
    reader.setup(app)

    service.furnish(app)
    service.run(app)


if __name__ == '__main__':
    main()
