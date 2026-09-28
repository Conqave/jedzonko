from contextlib import AbstractContextManager

from django.db import transaction

from shared.transactions import TransactionManager


class DjangoTransactionManager(TransactionManager):
    def atomic(self) -> AbstractContextManager[None]:
        return transaction.atomic()
