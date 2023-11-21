# Copyright 2021 - 2023 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Inbound adapter for the event subscriber"""
import logging

from ghga_event_schemas.validation import (
    EventSchemaValidationError,
    get_validated_payload,
)
from hexkit.custom_types import Ascii, JsonObject
from hexkit.protocols.eventsub import EventSubscriberProtocol
from pydantic import Field
from pydantic_settings import BaseSettings

from pci.context_vars import set_correlation_id
from pci.models import NonStagedFileRequested
from pci.ports.inbound.data_repository import DataRepositoryPort

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
log.setLevel(logging.INFO)


class EventSubTranslatorConfig(BaseSettings):
    """Config for receiving events."""

    file_events_topic: str = Field(..., description="The name of the events topic.")
    nonstaged_file_requested_type: str = Field(..., description="")


class EventSubTranslator(EventSubscriberProtocol):
    """A triple hexagonal translator compatible with the EventSubscriberProtocol."""

    def __init__(
        self,
        config: EventSubTranslatorConfig,
        data_repository: DataRepositoryPort,
    ):
        """Initialize with config parameters and core dependencies."""
        self._config = config
        self._data_repository = data_repository
        self.topics_of_interest = [config.file_events_topic]
        self.types_of_interest = [config.nonstaged_file_requested_type]

    async def _stage_file(self, *, payload: JsonObject):
        """Stage the requested file."""
        try:
            validated_payload = get_validated_payload(
                payload=payload, schema=NonStagedFileRequested
            )

            async with set_correlation_id(validated_payload.correlation_id):
                log.info("Set correlation ID to %s", validated_payload.correlation_id)

                with open(validated_payload.file_id, "w", encoding="utf-8") as file:
                    file.write(
                        f"The name of this file is {validated_payload.file_id}\n{validated_payload.correlation_id}"
                    )

        except EventSchemaValidationError:
            log.error(
                "Schema validation failed for %s", NonStagedFileRequested.__name__
            )

    async def _consume_validated(
        self,
        *,
        payload: JsonObject,
        type_: Ascii,
        topic: Ascii,
    ) -> None:
        if type_ == self._config.nonstaged_file_requested_type:
            await self._stage_file(payload=payload)
