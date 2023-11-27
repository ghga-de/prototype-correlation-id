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
"""Module hosting the dependency injection framework."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from ghga_service_commons.utils.context import asyncnullcontext
from hexkit.providers.akafka import KafkaEventPublisher, KafkaEventSubscriber

from pci.adapters.inbound.event_sub import EventSubTranslator
from pci.adapters.inbound.fastapi_ import dummies
from pci.adapters.inbound.fastapi_.configure import get_configured_app
from pci.adapters.outbound.event_pub import EventPubTranslator
from pci.config import Config
from pci.core.data_repository import DataRepository
from pci.ports.inbound.data_repository import DataRepositoryPort


@asynccontextmanager
async def prepare_core(*, config: Config) -> AsyncGenerator[DataRepositoryPort, None]:
    """Constructs and initializes all core components and their outbound dependencies."""
    async with KafkaEventPublisher.construct(config=config) as kafka_event_publisher:
        event_publisher = EventPubTranslator(
            config=config, provider=kafka_event_publisher
        )
        data_repository = DataRepository(config=config, event_publisher=event_publisher)

        yield data_repository


def prepare_core_with_override(
    *,
    config: Config,
    core_override: Optional[DataRepositoryPort] = None,
):
    """Resolve the prepare_core context manager based on config and override (if any)."""
    return (
        asyncnullcontext(core_override)
        if core_override
        else prepare_core(config=config)
    )


@asynccontextmanager
async def prepare_rest_app(
    *,
    config: Config,
    data_respository_override: Optional[DataRepositoryPort] = None,
) -> AsyncGenerator[FastAPI, None]:
    """Construct and initialize an REST API app along with all its dependencies.
    By default, the core dependencies are automatically prepared but you can also
    provide them using the override parameter.
    """
    app = get_configured_app(config=config)

    async with prepare_core_with_override(
        config=config, core_override=data_respository_override
    ) as data_repository:
        app.dependency_overrides[dummies.data_repository_port] = lambda: data_repository
        yield app


@asynccontextmanager
async def prepare_event_subscriber(
    *, config: Config, core_override: Optional[DataRepositoryPort] = None
):
    """Construct and initialize an event subscriber with all its dependencies.
    By default, the core dependencies are automatically prepared but you can also
    provide them using the core_override parameter.
    """
    async with prepare_core_with_override(
        config=config, core_override=core_override
    ) as data_repository:
        event_sub_translator = EventSubTranslator(
            data_repository=data_repository, config=config
        )
        async with KafkaEventSubscriber.construct(
            config=config, translator=event_sub_translator
        ) as kafka_event_subscriber:
            yield kafka_event_subscriber
