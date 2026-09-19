from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from households.composition import build_list_measurement_units


class MeasurementUnitListView(APIView):
    def get(self, request: Request) -> Response:
        units = build_list_measurement_units().execute()
        return Response(
            [
                {"code": unit.code, "name": unit.name, "dimension": unit.dimension.value}
                for unit in units
            ]
        )
