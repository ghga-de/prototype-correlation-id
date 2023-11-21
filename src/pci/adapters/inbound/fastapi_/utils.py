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


def is_valid_correlation_id(correlation_id: str):
    """Make sure the correlation ID is a valid UUID4."""
    try:
        UUID(correlation_id)
        return True
    except ValueError:
        return False


async def correlation_id_middleware(request: Request, call_next):
    """Check for correlation ID in the request headers.

    If the correlation ID doesn't exist or isn't valid, generate a new one.
    Set the header value if needed.
    Set the correlation ID ContextVar before passing on the request.
    """
    correlation_id = request.headers.get(CORRELATION_ID_HEADER_NAME, "")

    # Generate new id if needed
    if not is_valid_correlation_id(correlation_id):
        correlation_id = str(uuid4())
        log.warning("Generated new correlation id: %s", correlation_id)

        # Attach correlation ID to request state
        headers = dict(request.scope["headers"])
        headers[CORRELATION_ID_HEADER_NAME] = correlation_id
        request.scope["headers"] = [(k, v) for k, v in headers.items()]

    # Set the correlation ID in the context variable
    async with set_correlation_id(correlation_id):
        response = await call_next(request)
        return response
