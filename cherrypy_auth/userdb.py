import os
import datetime
import hashlib
import base64
import sqlite3
import traceback


class UserDatabase(object):

    EXPIRE_TIME = datetime.timedelta(minutes=15)

    def __init__(self, user_db_f):
        self.user_db_f = user_db_f
        if not(user_db_f is None):
            self.init_db()

    def init_db(self):
        
        # if not present, create data base file
        if not(os.path.exists(self.user_db_f)):
            open(self.user_db_f, 'w').close()
        
        # if not present, initialize user table
        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute('CREATE TABLE if not exists users(' +
                    'email TEXT UNIQUE, salt TEXT, password TEXT, ' +
                    'token TEXT, token_expire TIMESTAMP, ' +
                    'account_active INTEGER, ' +
                    'init_date date, last_seen date)')
        finally:
            con.close()

    def get_users(self):
        con = None
        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute('SELECT email, account_active FROM users')
            user_list = cur.fetchall()
        finally:
            con.close()

        return dict(user_list)

    def check_token(self, user, token):

        sql = 'SELECT token, token_expire FROM users WHERE email = ?'

        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute(sql, (user,))
            result = cur.fetchone()

            if(result is None):
                return False
            else:
                (db_token, expire_str) = result
                expire = datetime.datetime.strptime(expire_str,
                        '%Y-%m-%d %H:%M:%S.%f')
                if(expire < datetime.datetime.now()):
                    return False
                if not(db_token == token):
                    return False

        except sqlite3.Error:
            print traceback.print_exc()
            return False
        finally:
            if con:
                con.close()

        return True

    def activate_user(self, user, token):

        sql = 'UPDATE users SET account_active = 1 WHERE email = ?'

        if(self.check_token(user, token)):
            try:
                con = sqlite3.connect(self.user_db_f)
                cur = con.cursor()
                cur.execute(sql, (user,))
                con.commit()
                return True
            except sqlite3.Error:
                print traceback.print_exc()
                if con:
                    con.rollback()
                return False
            finally:
                if con:
                    con.close()
        else:
            return False

    def change_password_with_token(self, user, token, password):

        if(self.check_token(user, token)):
            return self.change_password(user, password)
        else:
            return False

    def change_password(self, user, password):

        sql0 = 'UPDATE users SET password = ? WHERE email = ?'
        sql1 = 'UPDATE users SET salt = ? WHERE email = ?'
        sql2 = 'UPDATE users SET token_expire = ? WHERE email = ?'

        salt, hashed_pw = self._hashed_salted_pw(password)
        token_expire = datetime.datetime.now()

        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute(sql0, (hashed_pw, user))
            cur.execute(sql1, (salt, user))
            cur.execute(sql2, (token_expire, user))
            con.commit()
            return True
        except sqlite3.Error:
            print traceback.print_exc()
            if con:
                con.rollback()
            return False
        finally:
            if con:
                con.close()

    def add_user(self, user, password):

        sql = 'INSERT INTO users values(?,?,?,?,?,?,?,?)'

        # collect data
        today = datetime.date.today()
        activation_token = self._generate_token()
        activation_expire = self._get_expire_time()
        active = 0
        salt, hashed_pw = self._hashed_salted_pw(password)

        # combine in a row
        row = (user, salt, hashed_pw, activation_token, activation_expire,
                active, today, today)

        # add the row to the users table
        con = None
        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute(sql, row)
            con.commit()
            return activation_token
        except sqlite3.Error:
            print traceback.print_exc()
            if con:
                con.rollback()
            return None
        finally:
            if con:
                con.close()

    def delete_user(self, user):
        sql = 'DELETE FROM users WHERE email = ?'
        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute(sql, (user,))
            con.commit()
            return True
        except sqlite3.Error:
            print traceback.print_exc()
            if con:
                con.rollback()
            return False
        finally:
            if con:
                con.close()

    def verify_password(self, user, password):

        # fetch user salt and hashed salted password
        sql = 'SELECT salt, password FROM users WHERE email = ?'
        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute(sql, (user,))
            result = cur.fetchone()
            if(result is None):
                return False
            else:
                (salt, db_hashed_pw) = result
        finally:
            con.close()

        _, user_hashed_pw = self._hashed_salted_pw(password, salt=salt)

        return user_hashed_pw == db_hashed_pw

    def user_active(self, user):
        sql = 'SELECT account_active FROM users WHERE email = ?'
        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute(sql, (user,))
            result = cur.fetchone()
            if(result is None):
                return False
            else:
                return result[0] == 1
        finally:
            con.close()

    def reset_token(self, user):

        # first check if user is active
        if not(self.user_active(user)):
            return None

        sql0 = 'UPDATE users SET token = ? WHERE email = ?'
        sql1 = 'UPDATE users SET token_expire = ? WHERE email = ?'

        token = self._generate_token()
        token_expire = self._get_expire_time()

        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute(sql0, (token, user))
            cur.execute(sql1, (token_expire, user))
            con.commit()
            return token
        except sqlite3.Error:
            print traceback.print_exc()
            if con:
                con.rollback()
            return None
        finally:
            if con:
                con.close()

    def update_last_seen(self, user):

        sql = 'UPDATE users SET last_seen = ? WHERE email = ?'
        now = datetime.datetime.now()

        # TODO return feedback?
        try:
            con = sqlite3.connect(self.user_db_f)
            cur = con.cursor()
            cur.execute(sql, (now, user))
            con.commit()
        except sqlite3.Error:
            print traceback.print_exc()
            if con:
                con.rollback()
        finally:
            if con:
                con.close()

    def _hashed_salted_pw(self, password, salt=None):
        if(salt is None):
            salt = os.urandom(64).encode('hex')
        salted_password = salt + password
        hashed_pw = hashlib.sha512(salted_password).hexdigest()
        return (salt, hashed_pw)

    def _get_expire_time(self):
        return datetime.datetime.now() + self.EXPIRE_TIME

    def _generate_token(self):
        return base64.urlsafe_b64encode(os.urandom(32))[:-1]
