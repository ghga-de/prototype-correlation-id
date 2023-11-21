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
"""Interface for broadcasting events to other services."""

from abc import ABC, abstractmethod

from ghga_event_schemas import pydantic_ as event_schemas


class EventPublisherPort(ABC):
    """A port through which service-internal events are communicated with the outside."""

    @abstractmethod
    async def non_staged_file_requested(
        self, *, event: event_schemas.NonStagedFileRequested
    ):
        """Publish an event communicating that there was a request for a file that has
        not yet been staged.
        """
