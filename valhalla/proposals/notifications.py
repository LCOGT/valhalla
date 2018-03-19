from django.template.loader import render_to_string

from valhalla.celery import send_mass_mail


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
        email_messages = []
        for user in users_to_notify(userrequest):
            email_tuple = (
                'Request {} has completed'.format(userrequest.group_id),
                message,
                'portal@lco.global',
                [user.email]
            )
            email_messages.append(email_tuple)
        if email_messages:
            send_mass_mail.delay(email_messages)
