"""AlMeezan: local AI output judge."""

from .core import evaluate_case
from .models import EvaluationCase, EvaluationResult

__all__ = ["EvaluationCase", "EvaluationResult", "evaluate_case"]

