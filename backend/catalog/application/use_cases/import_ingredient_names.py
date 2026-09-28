from catalog.application.ports.candidate_repository import CandidateRepository
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.candidate import ImportReport
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.names import CatalogName
from shared.transactions import TransactionManager


class ImportIngredientNames:

    def __init__(
        self,
        ingredients: IngredientRepository,
        candidates: CandidateRepository,
        transactions: TransactionManager,
    ) -> None:
        self._ingredients = ingredients
        self._candidates = candidates
        self._transactions = transactions

    def execute(self, names: tuple[str, ...], source: IngredientNameSource) -> ImportReport:
        parsed: dict[str, CatalogName] = {}
        for name in names:
            text = CatalogName.parse(name)
            parsed.setdefault(text.normalized_name, text)
        with self._transactions.atomic():
            known = self._ingredients.find_by_normalized_names(set(parsed))
            queued = self._candidates.existing_normalized_names(set(parsed) - set(known))
            created: list[str] = []
            for normalized_name, text in parsed.items():
                if normalized_name in known or normalized_name in queued:
                    continue
                self._candidates.create(text, source)
                created.append(text.name)
        return ImportReport(
            created=tuple(created),
            already_known=tuple(parsed[name].name for name in known),
            already_candidates=tuple(parsed[name].name for name in queued),
        )
