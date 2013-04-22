import os
import simplejson
import cherrypy
import ConfigParser

import userdb
import send_email


class Auth:

    SESSION_USER_KEY = 'user_id'

    def __init__(self, template_func, template_args, root_url, title,
                 user_db_f):

        # title as used above authentication forms on html pages
        self.title = title

        # the user data base sqlite file
        self.user_db_f = user_db_f

        # store template function and default arguments
        self.template_func = template_func
        self.template_args = template_args

        # store the root url
        self.root_url = root_url
        
        # initialize user database object and send email object
        self.udb = userdb.UserDatabase(self.user_db_f)

    def set_email_settings(self, smtp_server, port, fr, user, password):
        self.email = send_email.Email(smtp_server, port, fr, user, password)

    @cherrypy.expose
    def register(self):
        template = 'register.html'
        return self.template_func(template, **self._template_args())

    @cherrypy.expose
    def aregister(self, username, password):

        cherrypy.response.headers['Content-Type'] = 'application/json'

        location = ''
        msg = ''

        if(username == ''):
            msg = 'You forgot to enter an email address'
        else:

            exists = False

            all_users_dict = self.udb.get_users()
            if username in all_users_dict.keys():
                if(all_users_dict[username] == 0):
                    # remove inactivated user before adding him again
                    self.udb.delete_user(username)
                else:
                    msg = "Email address allready exists"
                    exists = True

            # add user and redirect to login if user does not exist yet
            if not(exists):

                # first logout, in case still logged in
                self._logout()

                # add the user to the database
                token = self.udb.add_user(username, password)

                if not(token is None):

                    # send activation email
                    url = '%sactivate_account/%s/%s' %\
                            (self.root_url, username, token)
                    to = username
                    subject = 'Activation SPiCa user account'
                    content = u'''
<p>Dear user,</p>

<p>To activate your SPiCa account, either click the following link or copy and 
paste it into your web browser.</p>

<a href=%s>%s</a>

<p>SPiCa</p>
''' % (url, url)

                    # try to send the email
                    msg = self.email.send_email(to, subject, content)

                    if(msg == ''):
                        # redirect location
                        location = '%sactivate_account' % (self.root_url)

                else:
                    msg = 'Something went wrong during registration, ' +\
                            'please try again'

        return simplejson.dumps(dict(msg=msg, location=location))

    @cherrypy.expose
    def activate_account(self, user=None, token=None):

        template = 'verify_email_address.html'
        kw_args = self._template_args()

        # show message if no parameters provided
        if(user is None and token is None):
            msg = 'A verification link has been send to your email ' +\
            'address. Please click on the link in the email or copy and ' +\
            'paste the link into the browser address bar to activate ' +\
            'your account.'
        # try to activate account otherwise
        else:
            if(self.udb.user_active(user)):
                msg = 'This account has allready been activated.'
            elif(self.udb.activate_user(user, token)):
                msg = 'Account successfully activated.'
            else:
                msg = 'Activation was not successful.'

        kw_args['msg'] = msg
        return self.template_func(template, **kw_args)

    @cherrypy.expose
    def forgot_password(self):
        template = 'forgot_password.html'
        return self.template_func(template, **self._template_args())

    @cherrypy.expose
    def aforgot_password(self, username):

        cherrypy.response.headers['Content-Type'] = 'application/json'

        # fetch all registered users
        token = self.udb.reset_token(username)
        location = ''
        error_msg = ''

        # check if provided user is in there
        if(username == ''):
            error_msg = 'You forgot to enter your email address.'
        elif(token is None):
            error_msg = 'This account does not exist or is not activated yet.'
        else:
            # send email with link
            url = '%schange_password_once?username=%s&token=%s' %\
                    (self.root_url, username, token)

            to = username
            subject = 'Change SPiCa account password'
            content = '<a href=%s>change password</a>' % (url)

            self.email.send_email(to, subject, content)

            # redirect location
            location = '%slogin' % (self.root_url)

        return simplejson.dumps(dict(msg=error_msg, location=location))

    @cherrypy.expose
    def change_password_once(self, username, token):
        template = 'change_password_once.html'
        return self.template_func(template, **self._template_args())

    @cherrypy.expose
    def achange_password_once(self, username, password, token):

        cherrypy.response.headers['Content-Type'] = 'application/json'

        msg = ''
        location = ''

        if(self.udb.change_password_with_token(username, token, password)):
            location = '%slogin' % (self.root_url)
        else:
            msg = 'Something went wrong, please try again.'

        return simplejson.dumps(dict(msg=msg, location=location))

    @cherrypy.expose
    def change_password(self):
        self._authenticate()
        template = 'change_password.html'
        return self.template_func(template, **self._template_args())

    @cherrypy.expose
    def achange_password(self, password):
        self._authenticate()
        cherrypy.response.headers['Content-Type'] = 'application/json'

        msg = ''
        location = ''

        if(self.udb.change_password(self.get_user(), password)):
            msg = 'Password successfully updated.'
            location = 'account'
        else:
            msg = 'Something went wrong, please try again.'

        return simplejson.dumps(dict(msg=msg, location=location))

    @cherrypy.expose
    def login(self):
        template = 'login.html'
        return self.template_func(template, **self._template_args())

    @cherrypy.expose
    def alogin(self, username, password):

        cherrypy.response.headers['Content-Type'] = 'application/json'

        msg = ''
        location = ''

        if(username == ''):
            msg = 'You forgot to enter your email address.'
        elif(self.udb.verify_password(username, password)):

            if not(self.udb.user_active(username)):
                msg = 'This account has not been activated yet.'

            else:

                location = '%s' % (self.root_url)

                # first logout, in case still logged in
                self._logout()

                # login
                cherrypy.session.regenerate()
                cherrypy.session[self.SESSION_USER_KEY] =\
                        cherrypy.request.login = username

                # set last seen to now in the database
                self.udb.update_last_seen(username)
        else:
            msg = 'Username and/or password incorrect.'

        return simplejson.dumps(dict(msg=msg, location=location))

    @cherrypy.expose
    def account(self):
        self._authenticate()
        template = 'account.html'
        return self.template_func(template, **self._template_args())

    @cherrypy.expose
    def delete_account(self):
        self._authenticate()
        template = 'delete_account.html'
        return self.template_func(template, **self._template_args())

    @cherrypy.expose
    def adelete_account(self, username, password):

        cherrypy.response.headers['Content-Type'] = 'application/json'

        # user must be loged in to perform this operation
        self._authenticate()
        # redirect to login (so that msg can be shown)
        location = ''
        msg = ''

        # delete account, using check username and password
        if(self.udb.verify_password(username, password)):
            self._logout()
            if(self.udb.delete_user(username)):
                msg = 'Account succesfully deleted'
                location = '%s' % (self.root_url)
            else:
                msg = 'Something went wrong'
        else:
            msg = 'Password incorrect, could not delete account'
        return simplejson.dumps(dict(msg=msg, location=location))

    @cherrypy.expose
    def logout(self):
        self._logout()
        raise cherrypy.HTTPRedirect("%s" % (self.root_url))

    def _authenticate(self):
        user = self.get_user()
        if not user:
            raise cherrypy.HTTPRedirect('%slogin' % (self.root_url))
        else:
            return user

    def _logout(self):
        sess = cherrypy.session
        username = sess.get(self.SESSION_USER_KEY, None)
        sess[self.SESSION_USER_KEY] = None
        if username:
            cherrypy.request.login = None

    def get_user(self):
        return cherrypy.session.get(self.SESSION_USER_KEY, None)

    def _template_args(self):
        kw_args = self.template_args.copy()
        kw_args['auth_title'] = self.title
        kw_args['user_id'] = self.get_user()
        return kw_args
