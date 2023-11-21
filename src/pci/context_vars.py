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
"""Functions to work with correlation ID.

These should be moved into a library like GHGA-Service-Commons.
"""
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

__all__ = [
    "set_context_var",
    "set_correlation_id",
    "get_correlation_id",
]


@asynccontextmanager
async def set_context_var(context_var: ContextVar, value: Any):
    """An async context manager to simplify the use of ContextVars"""
    token = context_var.set(value)
    yield
    context_var.reset(token)


@asynccontextmanager
async def set_correlation_id(correlation_id: str):
    """Set the correlation ID."""
    async with set_context_var(correlation_id_var, correlation_id):
        yield


def get_correlation_id() -> str:
    """Get the correlation ID.

    Having this as a separate function removes the need to work with the ContextVar directly.
    """
    return correlation_id_var.get()
