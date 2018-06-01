
from socket import gethostname
from email.message import EmailMessage
from smtplib import SMTP

from .utils import format_time_epoch
from .args import EMAIL, EMAILFROM, SMTPPORT, SMTPADDRESS, RETRIEVE, RECHECKPERIOD, LIST_RETRIEVE, LIST_SUBSCRIBE, \
    DAEMON

"""
Support for emailing the user after a download finishes.
"""


class Emailer:

    def __init__(self, config):
        self._email_to = config.arg(EMAIL)
        self._email_from = config.arg(EMAILFROM)
        self._smtp_address = config.arg(SMTPADDRESS)
        self._smtp_port = config.arg(SMTPPORT)
        self._log = config.log
        self._recheck_period = config.arg(RECHECKPERIOD)

    def __bool__(self):
        """
        We are enabled if an email is defined.
        """
        return bool(self._email_to)

    def send(self, subject, msg):
        """
        Send the email using the pre-configured parameters.
        """
        try:
            email = EmailMessage()
            email.set_content(msg)
            email['Subject'] = subject
            email['From'] = self._email_from
            email['To'] = self._email_to
            self._log.info('Sending completion email to %s (subject %s)' % (self._email_to, subject))
            smtp = SMTP(self._smtp_address)
            smtp.send_message(email)
            smtp.quit()
        except Exception as e:
            self._log.error('Error sending email to %s: %s' % (self._email_to, e))

    @staticmethod
    def describe_retrieve(source):
        msg = '''
A rover %s task started at %s has completed on %s.

The task comprised of %d SNCLs with data covering %ds.

A total of %d downloads were made, with %d errors.
''' % (RETRIEVE, format_time_epoch(source.start_epoch), gethostname(),
       source.initial_stats[0], source.initial_stats[1],
       source.n_downloads, source.n_errors)
        if source.n_errors:
            msg += '''
WARNING: Since the download had some errors, it may be incomplete.
         To check for completeness use `rover %s`
         Re-run the %s command to ensure completeness.
''' % LIST_RETRIEVE
        return 'Rover %s complete' % RETRIEVE, msg

    def describe_daemon(self, source):
        msg = '''
Subscription %s has been processed by the rover %s on %s.

The task comprised of %d SNCLs with data covering %ds.

A total of %d downloads were made, with %d errors.

The subscription will be checked again in %d hours.
''' % (source.name, DAEMON, gethostname(),
       source.initial_stats[0], source.initial_stats[1],
       source.n_downloads, source.n_errors,
       self._recheck_period)
        if source.n_errors:
            msg += '''
WARNING: Since the download had some errors, it may be incomplete.
         To check for completeness use `rover %s`
''' % LIST_SUBSCRIBE
        return 'Rover subscription %s processed' % source.name, msg
