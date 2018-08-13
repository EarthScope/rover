
from sys import version_info
from socket import gethostname

if version_info[0] >= 3:
    from email.message import EmailMessage
else:
    from email.mime.text import MIMEText
from smtplib import SMTP

from .manager import INCONSISTENT, UNCERTAIN
from .utils import format_time_epoch, format_time_epoch_local
from .args import EMAIL, EMAILFROM, SMTPPORT, SMTPADDRESS, RETRIEVE, RECHECKPERIOD, LIST_RETRIEVE, LIST_SUBSCRIBE, \
    DAEMON, RESUBSCRIBE, mm, DOWNLOADRETRIES


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
        self._recheck_period = config.arg(RECHECKPERIOD)
        self._log = config.log

    def send_email(self, subject, msg):
        """
        Send the email using the pre-configured parameters.
        """
        if not self._email_to:
            self._log.info('Not sending email (see %s)' % mm(EMAIL))
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
                self._log.default('Sending completion email to %s (subject %s)' % (self._email_to, subject))
                smtp = SMTP(self._smtp_address, port=self._smtp_port)
                if version_info[0] >= 3:
                    smtp.send_message(email)
                else:
                    smtp.sendmail(self._email_from, [self._email_to], email.as_string())
                smtp.quit()
            except Exception as e:
                self._log.error('Error sending email to %s via %s:%d: %s' %
                                (self._email_to, self._smtp_address, self._smtp_port, e))
                self._log.error('Consider using %s and %s (see your local network admin)'
                                % (mm(SMTPADDRESS), mm(EMAILFROM)))

    @staticmethod
    def _log_message(msg, logger):
        for line in msg.split('\n'):
            line = line.rstrip()
            logger(line)

    def describe_retrieve(self, source):
        """
        Generate the message sent by `rover retrieve`.
        """
        msg = '''
----- Retrieval Finished -----
        
A rover %s task on %s started %s 
(%s local) has completed.

The task comprised of %d N_S_L_Cs with data covering %ds.

A total of %d downloads were made, with %d errors (%d on
final pass of %d).
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
        elif source.consistent == INCONSISTENT:
            msg += '''
WARNING: Inconsistent behaviour was detected in the web 
         services (eg dataselect not providing data promised 
         by availability)
'''
        elif source.consistent == UNCERTAIN:
            msg += '''
The consistency of the web services could not be confirmed.
Re-run the %s command with %s > 1 to 
check
''' % (RETRIEVE, mm(DOWNLOADRETRIES))
        self._log_message(msg, self._log.warn if source.n_final_errors else self._log.default)
        return 'Rover %s complete' % RETRIEVE, msg

    def describe_daemon(self, source):
        """
        Generate the message sent by the daemon.
        """
        msg = '''
----- Subscription Processed -----
        
Subscription %s has been processed by the rover %s on %s.

The task comprised of %d N_S_L_Cs with data covering %ds.

A total of %d downloads were made, with %d errors (%d on
final pass of %d).

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
        elif source.consistent == INCONSISTENT:
            msg += '''
WARNING: Inconsistent behaviour was detected in the web 
         services (eg dataselect not providing data promised 
         by availability)
'''
        elif source.consistent == UNCERTAIN:
            msg += '''
The consistency of the web services could not be confirmed
(daemon must have %s > 1).
''' % mm(DOWNLOADRETRIES)
        self._log_message(msg, self._log.warn if source.n_final_errors else self._log.default)
        return 'Rover subscription %s processed' % source.name, msg
