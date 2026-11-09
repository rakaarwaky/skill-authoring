
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
)
from shared.src.discovery.taxonomy_discovery_request import DiscoveryRequest
from shared.src.discovery.taxonomy_discovery_response import DiscoveryResponse

#: Ranking field weights the discover capability exposes (re-exported for discovery).
DISCOVERY_FIELD_WEIGHTS = dict(BM25F_FIELD_WEIGHTS)
#: Fuzzy-match threshold the discover capability uses (re-exported for discovery).
DISCOVERY_SIMILARITY_THRESHOLD = SIMILARITY_THRESHOLD
#: Minimum fuzzy-match token length (re-exported for discovery).
DISCOVERY_MIN_TOKEN_LEN = MIN_TOKEN_LEN

__all__ = [
    "DISCOVERY_FIELD_WEIGHTS",
    "DISCOVERY_MIN_TOKEN_LEN",
    "DISCOVERY_SIMILARITY_THRESHOLD",
    "ISkillsCatalogProtocol",
    "ISkillsDiscoverProtocol",
    "ISkillsDiscoveryAggregate",
    "ISkillsListerProtocol",
    "ISkillsReaderProtocol",
]

class ISkillsDiscoveryAggregate(ABC):
    """Single entry point over discovery-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
