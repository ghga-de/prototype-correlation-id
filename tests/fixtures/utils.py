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

"""Utils for Fixture handling."""

from pathlib import Path

from fastapi import Request

from pci.adapters.inbound.fastapi_.utils import (
    CORRELATION_ID_HEADER_NAME,
    correlation_id_middleware,
    set_header_correlation_id,
)

BASE_DIR = Path(__file__).parent.resolve()

PATCH_LOCATION = "pci.adapters.inbound.fastapi_.configure.correlation_id_middleware"


async def replacement_middleware(request: Request, call_next, replacement_id: str):
    """Wrapper patch for `correlation_id_middleware`."""
    # Modify the correlation ID for testing purposes

    set_header_correlation_id(request, replacement_id)

    # make sure the value is set
    assert request.headers.get(CORRELATION_ID_HEADER_NAME) == replacement_id

    # pass the request on to the real middleware function
    return await correlation_id_middleware(request, call_next)
