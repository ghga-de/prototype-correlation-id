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
"""Adapter for publishing events to other services."""

import json

from hexkit.protocols.eventpub import EventPublisherProtocol
from pydantic import Field
from pydantic_settings import BaseSettings

from pci.models import NonStagedFileRequested
from pci.ports.outbound.event_pub import EventPublisherPort


class EventPubTranslatorConfig(BaseSettings):
    """Config for publishing internal events to the outside."""

    file_events_topic: str = Field(..., description="Name of the topic")
    nonstaged_file_requested_type: str = Field(..., description="Name of the event")


class EventPubTranslator(EventPublisherPort):
    """A translator according to the triple hexagonal architecture implementing
    the EventPublisherPort.
    """

    def __init__(
        self, *, config: EventPubTranslatorConfig, provider: EventPublisherProtocol
    ):
        """Initialize with configs and a provider of the EventPublisherProtocol."""
        self._config = config
        self._provider = provider

    async def non_staged_file_requested(self, *, event: NonStagedFileRequested):
        """Publish an event communicating that there was a request for a file that has
        not yet been staged.
        """
        payload = json.loads(event.model_dump_json())
        await self._provider.publish(
            payload=payload,
            type_=self._config.nonstaged_file_requested_type,
            topic=self._config.file_events_topic,
            key=event.file_id,
        )
