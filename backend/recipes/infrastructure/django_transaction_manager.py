from contextlib import AbstractContextManager

from django.db import transaction

from recipes.application.ports.transaction_manager import TransactionManager


class DjangoTransactionManager(TransactionManager):
    def atomic(self) -> AbstractContextManager[None]:
        return transaction.atomic()
