from django.template.loader import render_to_string

from valhalla.celery import send_mail


def users_to_notify(userrequest):
    all_proposal_users = set(userrequest.proposal.users.filter(profile__notifications_enabled=True))
    single_proposal_users = set(pn.user for pn in userrequest.proposal.proposalnotification_set.all())
    return [
        user for user in all_proposal_users.union(single_proposal_users)
        if not user.profile.notifications_on_authored_only or
        (user.profile.notifications_on_authored_only and userrequest.submitter == user)
    ]


def userrequest_notifications(userrequest):
    if userrequest.state == 'COMPLETED':
        message = render_to_string(
            'proposals/userrequestcomplete.txt',
            {'userrequest': userrequest}
        )
        send_mail.delay(
            'Request {} has completed'.format(userrequest.group_id),
            message,
            'portal@lco.global',
            [u.email for u in users_to_notify(userrequest)]
        )
