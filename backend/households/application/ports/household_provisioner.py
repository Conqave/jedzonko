from abc import ABC, abstractmethod


class HouseholdProvisioner(ABC):
    @abstractmethod
    def provision(self, household_id: int) -> None:
        raise NotImplementedError
