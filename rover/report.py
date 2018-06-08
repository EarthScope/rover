
from sys import version_info
from socket import gethostname
if version_info[0] >= 3:
    from email.message import EmailMessage
else:
    from email.mime.text import MIMEText
from smtplib import SMTP

from .utils import format_time_epoch, format_time_epoch_local
from .args import EMAIL, EMAILFROM, SMTPPORT, SMTPADDRESS, RETRIEVE, RECHECKPERIOD, LIST_RETRIEVE, LIST_SUBSCRIBE, \
    DAEMON, RESUBSCRIBE, mm

"""
Support for emailing the user after a download finishes.

(This is not exposed as a direct rover command).
"""


class Reporter:
    """
    Encapsulate the email functionality needed by the system.
    """

    def __init__(self, config):
        self._email_to = config.arg(EMAIL)
        self._email_from = config.arg(EMAILFROM)
        self._smtp_address = config.arg(SMTPADDRESS)
        self._smtp_port = config.arg(SMTPPORT)
        self._log = config.log
        self._recheck_period = config.arg(RECHECKPERIOD)

    def send_email(self, subject, msg):
        """
        Send the email using the pre-configured parameters.
        """
        if not self._email_to:
            self._log.warn('Not sending email (see %s)' % mm(EMAIL))
        else:
            try:
                if version_info[0] >= 3:
                    email = EmailMessage()
                    email.set_content(msg)
                else:
                    email = MIMEText(msg, _subtype='plain', _charset='utf-8')
                email['Subject'] = subject
                email['From'] = self._email_from
                email['To'] = self._email_to
                self._log.info('Sending completion email to %s (subject %s)' % (self._email_to, subject))
                smtp = SMTP(self._smtp_address, port=self._smtp_port)
                smtp.send_message(email)
                smtp.quit()
            except Exception as e:
                self._log.error('Error sending email to %s via %s:%d: %s' %
                                (self._email_to, self._smtp_address, self._smtp_port, e))
                self._log.error('Consider using %s and %s (see your local network admin)'
                                % (mm(SMTPADDRESS), mm(EMAILFROM)))

    def _log_message(self, msg, logger):
        for line in msg.split('\n'):
            line = line.rstrip()
            logger(line)

    def describe_retrieve(self, source):
        """
        Generate the message sent by `rover retrieve`.
        """
        msg = '''
A rover %s task on %s started %s 
(%s local) has completed.

The task comprised of %d SNCLs with data covering %ds.

A total of %d downloads were made, with %d errors (%d on
final download of %d).
''' % (RETRIEVE, gethostname(), format_time_epoch(source.start_epoch),
       format_time_epoch_local(source.start_epoch),
       source.initial_stats[0], source.initial_stats[1],
       source.n_downloads, source.n_errors, source.n_final_errors, source.n_retries)
        if source.n_final_errors:
            msg += '''
WARNING: Since the final download had some errors, it may be
         incomplete.
         To check for completeness use `rover %s`
         Re-run the %s command to ensure completeness.
''' % (LIST_RETRIEVE, RETRIEVE)
        self._log_message(msg, self._log.warn if source.n_errors else self._log.info)
        return 'Rover %s complete' % RETRIEVE, msg

    def describe_daemon(self, source):
        """
        Generate the message sent by the daemon.
        """
        msg = '''
Subscription %s has been processed by the rover %s on %s.

The task comprised of %d SNCLs with data covering %ds.

A total of %d downloads were made, with %d errors (%d on
final download of %d).

The subscription will be checked again in %d hours.
''' % (source.name, DAEMON, gethostname(),
       source.initial_stats[0], source.initial_stats[1],
       source.n_downloads, source.n_errors, source.n_final_errors, source.n_retries,
       self._recheck_period)
        if source.n_final_errors:
            msg += '''
WARNING: Since the final download had some errors, it may be 
         incomplete.
         To check for completeness use `rover %s %s`
         Run `rover %s %s` to reprocess immediately.
''' % (LIST_SUBSCRIBE, source.name, RESUBSCRIBE, source.name)
        self._log_message(msg, self._log.warn if source.n_errors else self._log.info)
        return 'Rover subscription %s processed' % source.name, msg
