from __future__ import annotations
import threading
from uuid import uuid4
import httpx
from django.conf import settings
from households.models import IngredientTag, Product, ProductTag
from shopping.models import ShoppingListItem

_jobs: dict[str, dict[str, object]] = {}

def _run(job_id: str, household_id: int, product_id: int | None = None) -> None:
    job = _jobs[job_id]
    products_query = Product.objects.filter(household_id=household_id)
    if product_id is not None:
        products_query = products_query.filter(id=product_id)
    products = list(products_query.order_by("id"))
    tags = list(IngredientTag.objects.filter(source="ania_gotuje").values("id", "name"))
    job["total"] = len(products)
    try:
        with httpx.Client(timeout=settings.ALIAS_MATCHER_HTTP_TIMEOUT_SECONDS) as client:
            for product in products:
                prompt = "Wybierz jeden tag z listy. Odpowiedz wyłącznie numerem albo 0.\nProdukt: %s\n" % product.name + "\n".join(f"{i+1}. {tag['name']}" for i, tag in enumerate(tags))
                response = client.post(f"{settings.ALIAS_MATCHER_BASE_URL.rstrip('/')}/api/chat", json={"model": settings.ALIAS_MATCHER_MODEL, "stream": False, "think": settings.ALIAS_MATCHER_REASONING_EFFORT, "messages": [{"role": "user", "content": prompt}]})
                content = response.json().get("message", {}).get("content", "")
                numbers = [int(part) for part in content.split() if part.isdigit()]
                choice = numbers[-1] if numbers else 0
                if 1 <= choice <= len(tags):
                    ProductTag.objects.update_or_create(product=product, ingredient_tag_id=tags[choice-1]["id"], defaults={"source": "ollama", "is_verified": False})
                job["processed"] = int(job["processed"]) + 1
        job["status"] = "completed"
    except Exception as error:
        job["status"] = "failed"
        job["error"] = str(error)[:240]

def start(household_id: int, product_id: int | None = None, item_id: int | None = None, text: str | None = None) -> str:
    if product_id is None and item_id is not None and text:
        item = ShoppingListItem.objects.get(id=item_id, shopping_list__household_id=household_id)
        normalized_name = text.strip().lower()
        product, _ = Product.objects.get_or_create(
            household_id=household_id,
            normalized_name=normalized_name,
            defaults={"name": text.strip()},
        )
        item.product = product
        item.free_text = None
        item.save(update_fields=["product", "free_text"])
        product_id = product.id
    job_id = str(uuid4())
    _jobs[job_id] = {"id": job_id, "status": "running", "processed": 0, "total": 0, "error": None}
    threading.Thread(target=_run, args=(job_id, household_id, product_id), daemon=True).start()
    return job_id

def get(job_id: str) -> dict[str, object] | None:
    return _jobs.get(job_id)
