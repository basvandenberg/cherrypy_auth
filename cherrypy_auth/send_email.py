import ConfigParser
import smtplib
from email.mime.text import MIMEText


class Email(object):

    def __init__(self, config_f):
        config = ConfigParser.ConfigParser()
        config.read(config_f)
        self.smtp_server = config.get('email', 'smtp_server')
        self.port = config.getint('email', 'port')
        self.fr = config.get('email', 'from')
        self.user = config.get('email', 'user')
        self.password = config.get('email', 'password')

    def send_email(self, to, subject, content):

        msg = MIMEText(content, 'html')
        msg['Subject'] = subject
        msg['From'] = self.fr
        msg['To'] = to

        s = smtplib.SMTP(self.smtp_server, self.port)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(self.user, self.password)

        error_msg = ''

        try:
            s.sendmail(self.fr, to, msg.as_string())
        except smtplib.SMTPRecipientsRefused:
            error_msg = 'Unable to send email to this address'
        finally:
            s.close()

        return error_msg
