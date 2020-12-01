import inspect
import inspect
import logging
from asyncio import CancelledError
from typing import Text, Dict, Any, Optional, Callable, Awaitable

import requests
from rasa.core.channels import UserMessage, InputChannel
from rasa.core.channels.channel import OutputChannel
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse

try:
    from urlparse import urljoin  # pytype: disable=import-error
except ImportError:
    from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class AiryBot(OutputChannel):

    @classmethod
    def name(cls) -> Text:
        return "airy"

    def __init__(self, auth_token: Text, api_host: Text) -> None:
        self.auth_token = auth_token
        self.api_host = api_host

    async def send_text_message(self, recipient_id: Text, text: Text, **kwargs: Any) -> None:
        headers = {
            "X-AUTH-AIRY": self.auth_token
        }

        body = {
            "conversation_id": recipient_id,
            "message": {
                "text": text
            }
        }
        requests.post("http://{}/messages.send".format(self.api_host), headers=headers, json=body)


class AiryInput(InputChannel):
    """A custom http input channel.

    This implementation is the basis for a custom implementation of a chat
    frontend. You can customize this to send messages to Rasa Core and
    retrieve responses from the agent."""

    @classmethod
    def name(cls) -> Text:
        return "airy"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        if not credentials:
            cls.raise_missing_credentials_exception()

        # pytype: disable=attribute-error
        return cls(
            credentials.get("auth_token"),
            credentials.get("api_host"),
        )
        # pytype: enable=attribute-error

    def __init__(self, auth_token: Text, api_host: Text) -> None:
        self.auth_token = auth_token
        self.api_host = api_host

    def _extract_conversation_id(self, req: Request) -> Optional[Text]:
        return req.json["conversation_id"]

    def _is_user_message(self, req: Request) -> bool:
        # For contact messages: sender id == conversation id
        # For user messages: sender id == user id
        return self._extract_conversation_id(req) != req.json["sender"]["id"]

    def blueprint(
            self, on_new_message: Callable[[UserMessage], Awaitable[None]]
    ) -> Blueprint:
        airy_webhook = Blueprint(
            "custom_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        # noinspection PyUnusedLocal
        @airy_webhook.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @airy_webhook.route("/webhook", methods=["POST"])
        async def receive(request: Request) -> HTTPResponse:
            conversation_id = request.json["conversation_id"]
            text = request.json.get("text", None)

            # Skip messages that are not sent from the source contact
            # but from an Airy user
            if self._is_user_message(request):
                return response.text("success")

            input_channel = self.name()
            metadata = self.get_metadata(request)

            airy_out = self.get_output_channel()
            # noinspection PyBroadException
            try:
                await on_new_message(
                    UserMessage(
                        text,
                        airy_out,
                        conversation_id,
                        input_channel=input_channel,
                        metadata=metadata,
                    )
                )
            except CancelledError:
                logger.error(
                    "Message handling timed out for "
                    "user message '{}'.".format(text)
                )
            except Exception:
                logger.exception(
                    "An exception occured while handling "
                    "user message '{}'.".format(text)
                )

            return response.text("success")

        return airy_webhook

    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        return {
            "source": request.json["source"]
        }

    def get_output_channel(self) -> Optional["OutputChannel"]:
        return AiryBot(self.auth_token, self.api_host)
