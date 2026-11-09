
from abc import ABC, abstractmethod

from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.discovery.taxonomy_discovery_constant import (
    BM25F_FIELD_WEIGHTS,
    MIN_TOKEN_LEN,
    SIMILARITY_THRESHOLD,
    STOP_WORDS,
)
from shared.src.discovery.taxonomy_discovery_request import DiscoveryRequest
from shared.src.discovery.taxonomy_discovery_response import DiscoveryResponse

__all__ = [
    "BM25F_FIELD_WEIGHTS",
    "ISkillsCatalogProtocol",
    "ISkillsDiscoverProtocol",
    "ISkillsDiscoveryAggregate",
    "ISkillsListerProtocol",
    "ISkillsReaderProtocol",
    "MIN_TOKEN_LEN",
    "SIMILARITY_THRESHOLD",
    "STOP_WORDS",
]

class ISkillsDiscoveryAggregate(ABC):
    """Single entry point over discovery-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
