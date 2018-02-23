from pyramid.config import Configurator
from pyramid.events import NewRequest
import ott.utils.object_utils as obj

import logging
log = logging.getLogger(__file__)

# globals the config/*.ini file
CONFIG = None


def add_cors_headers_response_callback(event):
    """
    add CORS so the requests can work from different (test / development) port
    do this at least for testing ... might not make call in production
    :param event:

    :see config.add_subscriber(add_cors_headers_response_callback, NewRequest):
    """
    def cors_headers(request, response):
        response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '1728000',
        })
    event.request.add_response_callback(cors_headers)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    global CONFIG
    CONFIG = settings

    # import pdb; pdb.set_trace()
    config = Configurator(settings=settings)

    # logging config for pserve / wsgi
    if settings and 'logging_config_file' in settings:
        from pyramid.paster import setup_logging
        setup_logging(settings['logging_config_file'])

    import views
    config.include(views.do_view_config)
    config.scan('pelias.adapter.pyramid')

    # CORS -- might not make this call in production (eliminate a bit of overheads, as CORS is handled by Apache)
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)

    return config.make_wsgi_app()
