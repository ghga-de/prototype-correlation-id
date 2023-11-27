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
"""Contains an event model used to simulate correlation ID in header."""
from ghga_event_schemas.pydantic_ import NonStagedFileRequested as Event
from pydantic import Field


class NonStagedFileRequested(Event):
    """A copy of NonStagedFileRequested with a `correlation_id` field added.

    The reason this is used is that the correlation ID would actually be stored in
    the header field of a Kafka event, and accessing event headers is not currently
    supported by hexkit.
    """

    correlation_id: str = Field(
        ...,
        description=(
            "A unique ID used to track the flow of events related to a single request."
        ),
    )
