"""Email notification support for deploygate checklists."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from deploygate.checklist import Checklist


@dataclass
class EmailConfig:
    """Configuration for sending email notifications."""

    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True
    sender: str = "deploygate@example.com"
    recipients: List[str] = field(default_factory=list)


def _build_subject(checklist: Checklist) -> str:
    status = "PASSED" if checklist.passed else "FAILED"
    return f"[DeployGate] {checklist.name} — {status}"


def _build_body(checklist: Checklist) -> str:
    lines = [
        f"Checklist: {checklist.name}",
        f"Status: {'✅ PASSED' if checklist.passed else '❌ FAILED'}",
        "",
        "Results:",
    ]
    for result in checklist.results:
        icon = "✅" if result.passed else "❌"
        line = f"  {icon} {result.name}"
        if result.message:
            line += f" — {result.message}"
        lines.append(line)
    return "\n".join(lines)


def notify(
    checklist: Checklist,
    config: EmailConfig,
    *,
    _smtp_cls=None,
) -> bool:
    """Send an email notification for the given checklist result.

    Returns True if the email was sent successfully, False otherwise.
    """
    if not config.recipients:
        return False

    smtp_cls = _smtp_cls or smtplib.SMTP

    subject = _build_subject(checklist)
    body = _build_body(checklist)

    msg = MIMEMultipart()
    msg["From"] = config.sender
    msg["To"] = ", ".join(config.recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtp_cls(config.smtp_host, config.smtp_port) as server:
            if config.use_tls:
                server.starttls()
            if config.smtp_user and config.smtp_password:
                server.login(config.smtp_user, config.smtp_password)
            server.sendmail(config.sender, config.recipients, msg.as_string())
        return True
    except smtplib.SMTPException:
        return False
