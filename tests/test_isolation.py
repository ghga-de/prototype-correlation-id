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
"""Test to verify that correlation IDs are preserved and contained in their contexts."""

import asyncio
import random

import pytest

from pci.context_vars import correlation_id_var, set_correlation_id


async def set_id_sleep_resume(correlation_id: str, use_context_manager: bool):
    """An async task to set the correlation ID ContextVar and yield control temporarily
    back to the event loop before resuming.
    """
    if use_context_manager:
        async with set_correlation_id(correlation_id):
            await asyncio.sleep(random.random() * 2)  # Yield control to the event loop
            # Check if the correlation ID is still the same
            assert correlation_id_var.get() == correlation_id, "Correlation ID changed"
    else:
        correlation_id_var.set(correlation_id)  # Set correlation ID for task
        await asyncio.sleep(random.random() * 2)  # Yield control to the event loop
        # Check if the correlation ID is still the same
        assert correlation_id_var.get() == correlation_id, "Correlation ID changed"


@pytest.mark.asyncio
async def test_correlation_id_isolation():
    """Make sure correlation IDs are isolated to the respective async task and that
    there's no interference from task switching.

    Test with a sleep time of 0-2s and a random combination of context
    manager/directly setting ContextVar.
    """
    tasks = [
        set_id_sleep_resume(f"test_{n}", random.choice((True, False)))
        for n in range(100)
    ]
    await asyncio.gather(*tasks)
