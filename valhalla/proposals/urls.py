from django.conf.urls import url
from django.views.decorators.http import require_POST

from valhalla.proposals.views import ProposalDetailView, ProposalListView, InviteCreateView
from valhalla.proposals.views import MembershipDeleteView, SemesterDetailView

urlpatterns = [
    url(r'^membership/(?P<pk>.+)/delete/$', MembershipDeleteView.as_view(), name='membership-delete'),
    url(r'^semester/(?P<pk>.+)/$', SemesterDetailView.as_view(), name='semester-detail' ),
    url(r'^$', ProposalListView.as_view(), name='list'),
    url(r'^(?P<pk>.+)/invite/$', require_POST(InviteCreateView.as_view()), name='invite'),
    url(r'^(?P<pk>.+)/$', ProposalDetailView.as_view(), name='detail'),
]
