from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.composition import build_list_ingredients, build_list_measurement_units


class IngredientListView(APIView):
    def get(self, request: Request) -> Response:
        name_query = request.query_params.get("search")
        ingredients = build_list_ingredients().execute(name_query)
        return Response(
            [
                {"id": item.id, "name": item.name, "default_unit_code": item.default_unit_code}
                for item in ingredients
            ]
        )


class MeasurementUnitListView(APIView):
    def get(self, request: Request) -> Response:
        units = build_list_measurement_units().execute()
        return Response(
            [
                {"code": unit.code, "name": unit.name, "dimension": unit.dimension.value}
                for unit in units
            ]
        )
