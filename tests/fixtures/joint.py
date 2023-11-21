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
"""Contains a JointFixture to bundle service providers for testing."""
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest_asyncio
from ghga_service_commons.api.testing import AsyncTestClient
from hexkit.providers.akafka import KafkaEventSubscriber
from hexkit.providers.akafka.testutils import KafkaFixture, kafka_fixture  # noqa: F401

from pci.config import Config
from pci.inject import (
    prepare_core,
    prepare_event_subscriber,
    prepare_rest_app,
)
from pci.ports.inbound.data_repository import DataRepositoryPort
from tests.fixtures.config import get_config


@dataclass
class JointFixture:
    """A class that bundles other service providers together."""

    config: Config
    data_repository: DataRepositoryPort
    event_subscriber: KafkaEventSubscriber
    kafka: KafkaFixture
    rest_client: AsyncTestClient


@pytest_asyncio.fixture
async def joint_fixture(
    kafka_fixture: KafkaFixture,  # noqa: F811
) -> AsyncGenerator[JointFixture, None]:
    """Fixture function to produce the JointFixture."""
    config = get_config(sources=[kafka_fixture.config])

    async with prepare_core(config=config) as data_repository:
        async with (
            prepare_rest_app(
                config=config, data_respository_override=data_repository
            ) as app,
            prepare_event_subscriber(
                config=config, core_override=data_repository
            ) as event_subscriber,
        ):
            async with AsyncTestClient(app=app) as rest_client:
                yield JointFixture(
                    config=config,
                    data_repository=data_repository,
                    event_subscriber=event_subscriber,
                    kafka=kafka_fixture,
                    rest_client=rest_client,
                )
