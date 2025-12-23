from email.message import EmailMessage
from os import getpid
from smtplib import SMTP
from socket import gethostname
from time import time

from .manager import ConsistencyState
from .utils import format_time_epoch, format_time_epoch_local
from .args import (
    EMAIL,
    EMAILFROM,
    SMTPPORT,
    SMTPADDRESS,
    RETRIEVE,
    LIST_RETRIEVE,
    mm,
    DOWNLOADRETRIES,
)


"""
Support for emailing the user after a download finishes.

(This is not exposed as a direct ROVER command).
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

    def send_email(self, subject, msg):
        """
        Send the email using the pre-configured parameters.
        """
        if not self._email_to:
            self._log.info("Not sending email (see %s)" % mm(EMAIL))
        else:
            try:
                email = EmailMessage()
                email.set_content(msg)
                email["Subject"] = subject
                email["From"] = self._email_from
                email["To"] = self._email_to
                self._log.default(
                    "Sending completion email to %s (subject %s)"
                    % (self._email_to, subject)
                )
                smtp = SMTP(self._smtp_address, port=self._smtp_port)
                smtp.send_message(email)
                smtp.quit()
            except Exception as e:
                self._log.error(
                    "Error sending email to %s via %s:%d: %s"
                    % (self._email_to, self._smtp_address, self._smtp_port, e)
                )
                self._log.error(
                    "Consider using %s and %s (see your local network admin)"
                    % (mm(SMTPADDRESS), mm(EMAILFROM))
                )

    @staticmethod
    def _log_message(msg, logger):
        for line in msg.split("\n"):
            line = line.rstrip()
            logger(line)

    @staticmethod
    def _human_duration(seconds):
        if seconds > 86400:
            return "{0:0.1f} days".format(seconds / 86400)
        elif seconds > 3600:
            return "{0:0.1f} hours".format(seconds / 3600)
        elif seconds > 60:
            return "{0:0.1f} minutes".format(seconds / 60)
        else:
            return "{0:0.2f} seconds".format(seconds)

    @staticmethod
    def _human_size(bytes):
        if bytes < 1000:
            return "{0:d} bytes".format(bytes)
        elif (bytes / 1024) < 1000:
            return "{0:0.1f} KiB".format(bytes / 1024)
        elif (bytes / 1024 / 1024) < 1000:
            return "{0:0.1f} MiB".format(bytes / 1024 / 1024)
        elif (bytes / 1024 / 1024 / 1024) < 1000:
            return "{0:0.1f} GiB".format(bytes / 1024 / 1024 / 1024)
        elif (bytes / 1024 / 1024 / 1024 / 1024) < 1000:
            return "{0:0.1f} TiB".format(bytes / 1024 / 1024 / 1024 / 1024)
        else:
            return "{0:0.1f} PiB".format(bytes / 1024 / 1024 / 1024 / 1024 / 1024)

    def describe_error(self, task, error):
        """
        Generate an email for critical errors.
        """
        return """
The ROVER %s (PID %d) task on %s has failed with the error:

  %s
  (%s)
""" % (task, getpid(), gethostname(), error, error.__class__.__name__)

    def describe_retrieve(self, source):
        """
        Generate the message sent by `rover retrieve`.
        """
        msg = """
----- Retrieval Finished -----


A ROVER %s task on %s
started %s (%s UTC)
has completed in %s

The download for %d stations totaled %s,
with data covering %d seconds.

A total of %d downloads were made, with %d errors (%d on final pass of %d).
""" % (
            RETRIEVE,
            gethostname(),
            format_time_epoch_local(source.start_epoch),
            format_time_epoch(source.start_epoch),
            self._human_duration(time() - source.start_epoch),
            source.initial_progress.stations[1],
            self._human_size(source.initial_progress.download_total_bytes),
            source.initial_progress.seconds[1],
            source.errors.downloads,
            source.errors.errors,
            source.errors.final_errors,
            source.n_retries,
        )
        if source.errors.final_errors:
            msg += """
WARNING: The final download had some errors, it may be incomplete.
         To check for completeness use `rover %s`
         Re-run the %s command to ensure completeness.
""" % (LIST_RETRIEVE, RETRIEVE)
        elif source.consistent == ConsistencyState.INCONSISTENT:
            msg += """
WARNING: Inconsistent retrieval was detected, most likely
         data indicated by the availability service was not
         available from the dataselect service.
"""
        elif source.consistent == ConsistencyState.UNCERTAIN:
            msg += """
The consistency of the web services could not be confirmed.
Re-run the %s command with %s > 1 to check
""" % (RETRIEVE, mm(DOWNLOADRETRIES))
        self._log_message(
            msg, self._log.warn if source.errors.final_errors else self._log.default
        )
        return "ROVER %s complete" % RETRIEVE, msg
