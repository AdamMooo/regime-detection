"""Gmail-SMTP HTML sender. Stdlib only (`smtplib` + `email`), no new dependency.

REIMPLEMENTED, not imported. `portfolio-manager/src/mailer.py` does the same job and was
read as a pattern, but this repo has no shared parent, no relative path out, and no code
dependency on the other two in either direction — importing it would create the coupling
the three-repo split exists to prevent.

Absent-secret posture: if the credentials are not in the environment, log and return
False. Sending is a delivery convenience; the ledger artifact is the product, and a
missing secret must never fail a build or a test. Every test uses the dry-run path.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

PASSWORD_ENV = "LEDGER_EMAIL_APP_PASSWORD"
ADDRESS_ENV = "LEDGER_EMAIL_ADDRESS"

logger = logging.getLogger(__name__)


def credentials():
    """(address, password) from the environment, or (None, None) if either is absent.

    Google prints app passwords in spaced groups of four and they paste that way; the
    spaces are display formatting, not part of the secret.
    """
    address = (os.environ.get(ADDRESS_ENV) or "").strip()
    password = (os.environ.get(PASSWORD_ENV) or "").replace(" ", "")
    if not address or not password:
        return None, None
    return address, password


def send_html(subject: str, html_body: str) -> bool:
    address, password = credentials()
    if address is None:
        logger.warning(
            "%s / %s not set - skipping send", ADDRESS_ENV, PASSWORD_ENV
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = address
    msg["To"] = address
    msg.set_content(
        "This message carries an HTML assumption ledger. "
        "Open it in a client that renders HTML."
    )
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(address, password)
            smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        logger.error("send failed: %s", exc)
        return False
    logger.info("sent to %s", address)
    return True
