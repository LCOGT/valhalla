from django.template.loader import render_to_string

from valhalla.celery import send_mail


def users_to_notify(proposal):
    all_proposal_users = set(proposal.users.filter(profile__notifications_enabled=True))
    single_proposal_users = {pn.user for pn in proposal.proposalnotification_set.all()}
    return all_proposal_users.union(single_proposal_users)


def userrequest_notifications(userrequest):
    if userrequest.state == 'COMPLETED':
        message = render_to_string(
            'proposals/userrequestcomplete.txt',
            {'userrequest': userrequest}
        )
        send_mail.delay(
            'Request {} has completed'.format(userrequest.group_id),
            message,
            'portal@lco.glboal',
            [u.email for u in users_to_notify(userrequest.proposal)]
        )
