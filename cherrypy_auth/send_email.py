import ConfigParser
import smtplib
from email.mime.text import MIMEText


class Email(object):

    def __init__(self, smtp_server, port, fr, user, password):
        self.smtp_server = smtp_server
        self.port = port
        self.fr = fr
        self.user = user
        self.password = password

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
