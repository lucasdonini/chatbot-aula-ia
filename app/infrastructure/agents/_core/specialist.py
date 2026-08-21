from dataclasses import dataclass

from .contracts.agent_node import AgentNode


@dataclass(frozen=True, slots=True)
class SpecialistRegistration:
    node: AgentNode
    description: str
    destination: str

    @property
    def name(self) -> str:
        return self.node.name
