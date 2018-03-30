from pyramid.config import Configurator
from pyramid.events import NewRequest
import ott.utils.object_utils as obj

import logging
log = logging.getLogger(__file__)


def add_cors_headers_response_callback(event):
    """
    add CORS so the requests can work from different (test / development) port
    do this at least for testing ... might not make call in production
    :param event:

    :see config.add_subscriber(add_cors_headers_response_callback, NewRequest):

    :see credit goes to https://stackoverflow.com/users/211490/wichert-akkerman
    :see https://stackoverflow.com/questions/21107057/pyramid-cors-for-ajax-requests
    """
    def cors_headers(request, response):
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '1728000',
        })

    # set the function above to be called for each response, where we'll set the CORS headers
    event.request.add_response_callback(cors_headers)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    #import pdb; pdb.set_trace()
    config = Configurator(settings=settings)

    # logging config for pserve / wsgi
    if settings and 'logging_config_file' in settings:
        from pyramid.paster import setup_logging
        setup_logging(settings['logging_config_file'])

    import views
    config.include(views.do_view_config)
    config.scan('pelias.adapter.pyramid')

    # CORS -- might not make this call in production (eliminate a bit of overheads, as CORS is handled by Apache)
    if settings and settings.get('enable_cors_headers') == 'true':
        config.add_subscriber(add_cors_headers_response_callback, NewRequest)

    return config.make_wsgi_app()
