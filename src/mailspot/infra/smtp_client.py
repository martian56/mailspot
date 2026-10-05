from __future__ import annotations

import aiosmtplib
from python_socks import ProxyError
from python_socks.async_.asyncio import Proxy

from .ports import SmtpReply

_SMTP_PORT = 25


class AioSmtpProber:
    async def probe(
        self,
        host: str,
        recipient: str,
        *,
        helo: str,
        mail_from: str,
        timeout: float,
        proxy: str | None,
    ) -> SmtpReply:
        transcript: list[tuple[str, int | None]] = []
        opened = await self._open(host, helo, timeout, proxy)
        if opened is None:
            return SmtpReply(connected=False, error="could not connect to the mail host")

        client, connect_code = opened
        transcript.append(("CONNECT", connect_code))
        try:
            ehlo = await client.ehlo()
            transcript.append(("EHLO", ehlo.code))
            mail = await client.mail(mail_from)
            transcript.append(("MAIL FROM", mail.code))
            rcpt = await client.rcpt(recipient)
            transcript.append(("RCPT TO", rcpt.code))
            return SmtpReply(
                connected=True, code=rcpt.code, message=rcpt.message, transcript=tuple(transcript)
            )
        except aiosmtplib.SMTPResponseException as exc:
            transcript.append(("RCPT TO", exc.code))
            return SmtpReply(
                connected=True, code=exc.code, message=exc.message, transcript=tuple(transcript)
            )
        except (aiosmtplib.SMTPException, OSError) as exc:
            return SmtpReply(connected=True, error=str(exc), transcript=tuple(transcript))
        finally:
            await self._close(client)

    async def _open(
        self, host: str, helo: str, timeout: float, proxy: str | None
    ) -> tuple[aiosmtplib.SMTP, int | None] | None:
        try:
            if proxy is not None:
                sock = await Proxy.from_url(proxy).connect(
                    dest_host=host, dest_port=_SMTP_PORT, timeout=timeout
                )
                client = aiosmtplib.SMTP(
                    sock=sock, timeout=timeout, local_hostname=helo, start_tls=False
                )
            else:
                client = aiosmtplib.SMTP(
                    hostname=host,
                    port=_SMTP_PORT,
                    timeout=timeout,
                    local_hostname=helo,
                    start_tls=False,
                )
            response = await client.connect()
            return client, response.code
        except (aiosmtplib.SMTPException, ProxyError, OSError):
            return None

    async def _close(self, client: aiosmtplib.SMTP) -> None:
        try:
            await client.quit()
        except (aiosmtplib.SMTPException, OSError):
            client.close()
