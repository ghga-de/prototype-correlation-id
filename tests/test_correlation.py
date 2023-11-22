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
"""Tests for the correlation ID."""
import asyncio
import os
from functools import partial
from tempfile import TemporaryDirectory

import pytest
from fastapi import Request
from hexkit.providers.akafka.testutils import KafkaFixture, kafka_fixture  # noqa: F401

from pci.adapters.inbound.fastapi_.utils import (
    CORRELATION_ID_HEADER_NAME,
    correlation_id_middleware,
    is_valid_correlation_id,
)
from pci.models import NonStagedFileRequested
from tests.fixtures.joint import JointFixture, joint_fixture  # noqa: F401


async def replacement_middleware(request: Request, call_next, replacement_id: str):
    """Wrapper patch for `correlation_id_middleware`."""
    # Modify the correlation ID for testing purposes
    headers = dict(request.scope["headers"])
    headers[CORRELATION_ID_HEADER_NAME] = ""
    request.scope["headers"] = [(k, v) for k, v in headers.items()]

    # make sure the value is set
    assert request.headers.get(CORRELATION_ID_HEADER_NAME) == replacement_id

    # pass the request on to the real middleware function
    return await correlation_id_middleware(request, call_next)


@pytest.mark.parametrize("replacement_id", ["", "invalid"])
@pytest.mark.asyncio
async def test_rest_call_without_correlation_id(
    joint_fixture: JointFixture,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    replacement_id: str,
):
    """Make sure a new ID is generated if a REST api request is received with a missing
    or invalid correlation ID.
    """
    monkeypatch.setattr(
        "pci.adapters.inbound.fastapi_.utils.correlation_id_middleware",
        partial(replacement_middleware, replacement_id=replacement_id),
    )

    response = await joint_fixture.rest_client.get("/test.txt")
    body = response.json()
    assert body["correlation_id"] != replacement_id
    assert is_valid_correlation_id(body["correlation_id"])


@pytest.mark.parametrize("replacement_id", ["", "invalid"])
@pytest.mark.asyncio
async def test_event_without_correlation_id(
    joint_fixture: JointFixture,  # noqa: F811
    replacement_id: str,
):
    """Make sure a new ID is generated if an event is received with a missing
    or invalid correlation ID.
    """
    event = NonStagedFileRequested(
        file_id="test",
        target_bucket_id="test",
        target_object_id="test",
        s3_endpoint_alias="test",
        decrypted_sha256="123",
        correlation_id=replacement_id,
    )

    # publish event with bad id
    await joint_fixture.kafka.publish_event(
        payload=event.model_dump(),
        type_=joint_fixture.config.nonstaged_file_requested_type,
        topic=joint_fixture.config.file_events_topic,
        key="",
    )
    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        filepath = f"{temp_dir}/test"
        await joint_fixture.event_subscriber.run(False)
        assert os.path.exists(filepath)
        with open(filepath, encoding="utf-8") as file:
            correlation_id = file.readlines()[-1]
            assert correlation_id != replacement_id
            assert is_valid_correlation_id(correlation_id)


@pytest.mark.asyncio
async def test_simultaneous_requests(joint_fixture: JointFixture):  # noqa: F811
    """Test with multiple requests at the same time."""
    test_volume = 40
    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        response_futures = [
            joint_fixture.rest_client.get(f"/test_{n}.txt") for n in range(test_volume)
        ]
        responses = [
            response.json() for response in await asyncio.gather(*response_futures)
        ]

        for response in responses:
            assert response["file_content"] == "file requested"
            assert response["correlation_id"] != ""

        # sanity check that there is a unique CID for every request
        assert (
            len(set([response["correlation_id"] for response in responses]))
            == test_volume
        )

        # consume the events
        consume_futures = [
            joint_fixture.event_subscriber.run(False) for _ in range(test_volume)
        ]

        await asyncio.gather(*consume_futures)

        # look at the returned file contents to verify the CIDs are as expected
        for n in range(test_volume):
            file_id = f"test_{n}.txt"
            response = await joint_fixture.rest_client.get(f"/{file_id}")
            body = response.json()
            old_correlation_id = responses[n]["correlation_id"]
            assert body["correlation_id"] != old_correlation_id
            assert (
                body["file_content"]
                == f"The name of this file is {file_id}\n{old_correlation_id}"
            )
