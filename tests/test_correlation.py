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
from tempfile import TemporaryDirectory

import pytest
from hexkit.providers.akafka.testutils import KafkaFixture, kafka_fixture  # noqa: F401

from tests.fixtures.joint import JointFixture, joint_fixture  # noqa: F401


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
