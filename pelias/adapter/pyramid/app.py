from pyramid.config import Configurator
from pyramid.events import NewRequest

from ott.utils.svr.pyramid import app_utils

import logging
log = logging.getLogger(__file__)



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
        config.add_subscriber(app_utils.add_cors_headers_response_callback, NewRequest)

    return config.make_wsgi_app()
