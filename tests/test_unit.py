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
"""Misc unit tests."""

import pytest
from fastapi import Request

from pci.adapters.inbound.fastapi_.utils import (
    CORRELATION_ID_HEADER_NAME,
    InvalidCorrelationIdError,
    set_header_correlation_id,
    validate_correlation_id,
)
from pci.context_vars import (
    MissingCorrelationIdError,
    get_correlation_id,
    set_correlation_id,
)


def dummy_request() -> Request:
    """Return a dummy request object to directly call middleware functions."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
    }
    return Request(scope=scope)


@pytest.mark.asyncio
async def test_correlation_id_validation():
    """Ensure an error is raised when correlation ID validation fails."""
    with pytest.raises(InvalidCorrelationIdError):
        validate_correlation_id("BAD_ID")


@pytest.mark.asyncio
async def test_getting_empty_correlation_id():
    """Ensure an error is raised when calling `get_correlation_id` for an empty id."""
    async with set_correlation_id(correlation_id=""):
        with pytest.raises(MissingCorrelationIdError):
            get_correlation_id()


def test_header_update_function():
    """Verify that the header update function works."""
    request = dummy_request()
    set_header_correlation_id(request, "id123")
    assert request.headers.get(CORRELATION_ID_HEADER_NAME) == "id123"
