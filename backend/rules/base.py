from abc import ABC, abstractmethod
from typing import List
from backend.models.violation import RuleViolation

class BaseRule(ABC):
    @property
    @abstractmethod
    def rule_number(self) -> str:
        pass

    @property
    @abstractmethod
    def rule_name(self) -> str:
        pass

    @property
    @abstractmethod
    def severity(self) -> str:
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def analyze(self, ast, source_code: str, file_name: str) -> List[RuleViolation]:
        """
        Analyze the AST of the C source code and return any violations found.
        """
        pass
