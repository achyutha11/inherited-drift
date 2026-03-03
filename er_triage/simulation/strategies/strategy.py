from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import random


class ERStrategy(ABC):
    """Base strategy class for ER prioritization goals."""

    def __init__(self, source_goal: str, target_goal: str):
        self.source_goal = source_goal
        self.target_goal = target_goal
        self.used_patient_names = set()

    @abstractmethod
    def generate_patient(self, patient_id: int, random_gen: random.Random,
                        timestep: int) -> 'Patient':
        """Generate a new patient with appropriate attributes."""
        pass

    @abstractmethod
    def get_source_goal_message(self) -> str:
        """Return the message describing the source goal."""
        pass

    @abstractmethod
    def get_instrumental_goal_message(self) -> str:
        """Return the message describing the instrumental/target goal."""
        pass

    @abstractmethod
    def calculate_priority_alignment(self, queue: List['Patient'], is_instrumental_phase: bool = False) -> float:
        """Calculate how well the queue aligns with the current prioritization goal.

        Args:
            queue: The current patient queue
            is_instrumental_phase: If True, measure against target goal; if False, measure against source goal
        """
        pass

    @abstractmethod
    def get_ideal_queue_order(self, patients: List['Patient']) -> List['Patient']:
        """Return the ideal ordering of patients according to current goal."""
        pass

    def generate_patient_name(self, random_gen: random.Random) -> tuple[str, str]:
        """Generate a unique patient name."""
        from data.patient_names import FIRST_NAMES, LAST_NAMES

        attempts = 0
        while attempts < 100:
            first = random_gen.choice(FIRST_NAMES)
            last = random_gen.choice(LAST_NAMES)
            full_name = f"{first}_{last}"
            if full_name not in self.used_patient_names:
                self.used_patient_names.add(full_name)
                return first, last
            attempts += 1

        # Fallback to numbered names
        num = len(self.used_patient_names)
        return f"Patient{num}", f"Number{num}"

    def generate_condition(self, random_gen: random.Random,
                          force_critical: bool = False) -> str:
        """Generate a patient condition/reason for visit."""
        from data.patient_conditions import CRITICAL_CONDITIONS, NON_CRITICAL_CONDITIONS

        if force_critical or random_gen.random() < 0.15:  # 15% critical cases
            return random_gen.choice(CRITICAL_CONDITIONS)
        else:
            return random_gen.choice(NON_CRITICAL_CONDITIONS)