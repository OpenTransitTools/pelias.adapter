from pyramid.config import Configurator
import ott.utils.object_utils as obj

import logging
log = logging.getLogger(__file__)

# database
DB = None
CONFIG = None
ECHO = True


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    # logging config for pserve / wsgi
    if settings and 'logging_config_file' in settings:
        from pyramid.paster import setup_logging
        setup_logging(settings['logging_config_file'])

    #import pdb; pdb.set_trace()
    global CONFIG
    global DB
    CONFIG = settings
    DB = connect(settings)

    import views
    config.include(views.do_view_config)
    config.scan('ott.services.pyramid')

    return config.make_wsgi_app()
