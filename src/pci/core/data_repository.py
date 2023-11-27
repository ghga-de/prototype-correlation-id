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
"""Describes the concrete data repository object."""


from pci.config import Config
from pci.context_vars import get_correlation_id
from pci.models import NonStagedFileRequested
from pci.ports.inbound.data_repository import DataRepositoryPort
from pci.ports.outbound.event_pub import EventPublisherPort


class DataRepository(DataRepositoryPort):
    """Concrete implementation of the data repository."""

    def __init__(self, *, config: Config, event_publisher: EventPublisherPort):
        self._config = config
        self._event_publisher = event_publisher

    async def handle_request(self, file_id: str) -> str:
        """Handle a request for a file.

        If the file doesn't exist, publish an event to request it.
        """
        try:
            with open(file_id, encoding="utf-8") as file:
                return file.read()
        except OSError:
            event = NonStagedFileRequested(
                correlation_id=get_correlation_id(),
                file_id=file_id,
                target_object_id=file_id,
                target_bucket_id="test",
                s3_endpoint_alias="test",
                decrypted_sha256="",
            )

            await self._event_publisher.non_staged_file_requested(event=event)
            return "file requested"
