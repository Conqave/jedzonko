from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from households.application.errors import (
    AliasProposalNotFoundError,
    AliasProposalNotPendingError,
    NotAHouseholdMemberError,
)
from households.composition import (
    build_accept_tag_proposal,
    build_list_tag_proposals,
    build_reject_tag_proposal,
)
from households.domain.alias_proposal import AliasProposal


def _current_user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return user_id


def _represent_proposal(proposal: AliasProposal) -> dict[str, object]:
    return {
        "id": proposal.id,
        "household_id": proposal.household_id,
        "requirement_name": proposal.requirement_name,
        "product_id": proposal.product_id,
        "product_name": proposal.product_name,
        "model_name": proposal.model_name,
        "created_at": proposal.created_at.isoformat(),
        "state": proposal.state.value,
    }


class TagProposalListView(APIView):
    def get(self, request: Request, household_id: int) -> Response:
        try:
            proposals = build_list_tag_proposals().execute(
                _current_user_id(request), household_id
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response([_represent_proposal(proposal) for proposal in proposals])


class TagProposalAcceptView(APIView):
    def post(self, request: Request, proposal_id: int) -> Response:
        try:
            proposal = build_accept_tag_proposal().execute(_current_user_id(request), proposal_id)
        except AliasProposalNotFoundError:
            raise NotFound(detail="Tag proposal not found.", code="tag_proposal_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except AliasProposalNotPendingError:
            raise ValidationError(
                detail="Tag proposal is already resolved.", code="tag_proposal_not_pending"
            )
        return Response(_represent_proposal(proposal))


class TagProposalRejectView(APIView):
    def post(self, request: Request, proposal_id: int) -> Response:
        try:
            proposal = build_reject_tag_proposal().execute(_current_user_id(request), proposal_id)
        except AliasProposalNotFoundError:
            raise NotFound(detail="Tag proposal not found.", code="tag_proposal_not_found")
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except AliasProposalNotPendingError:
            raise ValidationError(
                detail="Tag proposal is already resolved.", code="tag_proposal_not_pending"
            )
        return Response(_represent_proposal(proposal))


# Compatibility aliases for imports from pre-tag terminology. New routes and
# composition code should use the TagProposal names above.
AliasProposalListView = TagProposalListView
AliasProposalAcceptView = TagProposalAcceptView
AliasProposalRejectView = TagProposalRejectView
