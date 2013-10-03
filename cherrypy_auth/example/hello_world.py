import os
import cherrypy
from cherrypy.lib.static import serve_file
from mako.lookup import TemplateLookup
from cherrypy_auth import auth

root_url = 'http://localhost:8080/'
user_db_f = 'users.db'
config_f = 'hello_world.cfg'
tmpl_dir = 'templates'
auth_tmpl_dir = '/home/bastiaan/Development/cherrypy_auth_0.1/' +\
        'cherrypy_auth/template/mako'
SESSION_KEY = '_cp_username'

# create global template lookup object
mylookup = TemplateLookup(directories=[tmpl_dir, auth_tmpl_dir],
                          module_directory='/tmp/mako/')


def get_template(name, **kwargs):
    t = mylookup.get_template(name)
    return t.render(**kwargs)


def default_template_args():

    # retrieve user id from session data
    if(hasattr(cherrypy, 'session')):
        user_id = cherrypy.session.get(SESSION_KEY, None)
    else:
        user_id = None

    return {'user_id': user_id, 'root_url': root_url}


def authenticate():
    '''
    Authentication decorator, redirect to login if user is not logged in.
    '''
    user = cherrypy.session.get(SESSION_KEY, None)
    if not user:
        raise cherrypy.HTTPRedirect('%slogin' % (root_url))

cherrypy.tools.authenticate = cherrypy.Tool('before_handler', authenticate)


class HelloWorld(object):

    def __init__(self):

        # create authentication object
        a = auth.Auth(SESSION_KEY, user_db_f, get_template,
                default_template_args(), root_url, config_f)

        # authentication links (because I want them in root, not /auth/login)
        self.login = a.login
        self.alogin = a.alogin
        self.register = a.register
        self.aregister = a.aregister
        self.forgot_password = a.forgot_password
        self.aforgot_password = a.aforgot_password
        self.change_password = a.change_password
        self.achange_password = a.achange_password
        self.activate_account = a.activate_account
        self.logout = a.logout
        # the following are only accessible by authenticated users
        self.account = a.account
        self.change_password_once = a.change_password_once
        self.achange_password_once = a.achange_password_once
        self.delete_account = a.delete_account
        self.adelete_account = a.adelete_account

    @cherrypy.expose
    def index(self):
        return get_template('index.html', **default_template_args())

    @cherrypy.tools.authenticate()
    @cherrypy.expose
    def restricted(self):
        return get_template('restricted.html', **default_template_args())

if __name__ == '__main__':
    cherrypy.quickstart(HelloWorld(), config=config_f)
