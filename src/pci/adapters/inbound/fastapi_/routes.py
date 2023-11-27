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
"""API endpoints"""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from pci.adapters.inbound.fastapi_.dummies import DataRepositoryDummy
from pci.context_vars import get_correlation_id

router = APIRouter()


@router.get("/{file_id}")
async def request_file(
    request: Request,
    file_id: str,
    data_repository: DataRepositoryDummy,
):
    """Handle a request for a given file ID."""
    # correlation ID can be retrieved from the request header or from the ContextVar
    correlation_id = get_correlation_id()
    file_content = await data_repository.handle_request(file_id=file_id)

    return JSONResponse(
        content={
            "correlation_id": correlation_id,
            "file_content": file_content,
        },
        status_code=status.HTTP_200_OK,
    )
