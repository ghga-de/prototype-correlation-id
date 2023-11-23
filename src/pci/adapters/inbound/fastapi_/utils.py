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
"""Example middleware function for adding correlation ID to requests.

This should probably be moved to ghga-service-commons and used in the configure_app
function or somewhere similar.
"""
import logging
from uuid import UUID, uuid4

from fastapi import Request

from pci.context_vars import set_correlation_id

CORRELATION_ID_HEADER_NAME = "X-Correlation-ID"

log = logging.getLogger()


class InvalidCorrelationIdError(RuntimeError):
    """Raised when a correlation ID fails validation."""

    def __init__(self, *, correlation_id: str):
        message = f"Invalid correlation ID found: '{correlation_id}'"
        super().__init__(message)


def validate_correlation_id(correlation_id: str):
    """Raises an error if the correlation ID is invalid.

    Raises:
        InvalidCorrelationIdError: If the correlation ID is invalid.
    """
    try:
        UUID(correlation_id)
    except ValueError as err:
        raise InvalidCorrelationIdError(correlation_id=correlation_id) from err


def set_header_correlation_id(request: Request, correlation_id: str):
    """Set the correlation ID on the request header."""
    headers = request.headers.mutablecopy()
    headers[CORRELATION_ID_HEADER_NAME] = correlation_id
    request.scope.update(headers=headers.raw)
    # delete _headers to force update
    delattr(request, "_headers")
    log.info("Assigned %s as header correlation ID value.", correlation_id)


def get_validated_correlation_id(correlation_id: str) -> str:
    """Returns existing correlation ID if valid or generates a new one if nonexistent.

    Raises:
        InvalidCorrelationIdError: If a correlation ID exists but is invalid.
    """
    if correlation_id:
        validate_correlation_id(correlation_id)
    else:
        correlation_id = str(uuid4())
        log.warning("Generated new correlation id: %s", correlation_id)
    return correlation_id


async def correlation_id_middleware(request: Request, call_next):
    """Ensure request header has a valid correlation ID.

    Set the correlation ID ContextVar before passing on the request.

    Raises:
        InvalidCorrelationIdError: If a correlation ID exists and is invalid.
    """
    correlation_id = request.headers.get(CORRELATION_ID_HEADER_NAME, "")

    # If a correlation ID exists, validate it. If not, generate a new one.
    validated_correlation_id = get_validated_correlation_id(correlation_id)
    if validate_correlation_id != correlation_id:
        set_header_correlation_id(request, validated_correlation_id)

    # Set the correlation ID ContextVar
    async with set_correlation_id(validated_correlation_id):
        response = await call_next(request)
        return response
