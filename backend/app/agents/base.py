from abc import ABC, abstractmethod
from typing import Any, Dict
import os

class BaseAgent(ABC):
    """
    Abstract Base Class for Enterprise Agentic QE capabilities.
    Enforces unified interfaces, PACTS compliance, and clear distinction
    between Platform Agent integrations and Local Deterministic Fallbacks.
    """
    def __init__(self, name: str, capability: str, pacts_principle: str):
        self.name = name
        self.capability = capability
        self.pacts_principle = pacts_principle
        # Check if platform credentials/agent service is configured
        self.platform_agent_available = os.getenv("PLATFORM_AGENT_ENABLED", "false").lower() == "true"

    @property
    def execution_mode(self) -> str:
        return "Platform Agent" if self.platform_agent_available else "Local Deterministic Fallback"

    @abstractmethod
    def execute(self, input_data: Any) -> Dict[str, Any]:
        """Execute agent capability with input data."""
        pass
