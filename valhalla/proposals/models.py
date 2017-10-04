from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from django.urls import reverse
from collections import namedtuple
import logging

from valhalla.celery import send_mail

logger = logging.getLogger(__name__)


class Semester(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    start = models.DateTimeField()
    end = models.DateTimeField()
    proposals = models.ManyToManyField("Proposal", through="TimeAllocation")

    @classmethod
    def current_semesters(cls):
        return cls.objects.filter(start__lte=timezone.now(), end__gte=timezone.now())

    def __str__(self):
        return self.id


class TimeAllocationGroup(models.Model):
    id = models.CharField(max_length=20, primary_key=True)

    def __str__(self):
        return self.id


class Proposal(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    active = models.BooleanField(default=True)
    title = models.CharField(max_length=255, default='', blank=True)
    abstract = models.TextField(default='', blank=True)
    tac_priority = models.PositiveIntegerField(default=0)
    tac_rank = models.PositiveIntegerField(default=0)
    tag = models.ForeignKey(TimeAllocationGroup)
    public = models.BooleanField(default=False)
    users = models.ManyToManyField(User, through='Membership')

    class Meta:
        ordering = ('title',)

    @property
    def pi(self):
        return self.users.filter(membership__role=Membership.PI).first()

    @property
    def cis(self):
        return self.users.filter(membership__role=Membership.CI)

    @classmethod
    def current_proposals(cls):
        return cls.objects.filter(semester__in=Semester.current_semesters())

    def add_users(self, emails, role):
        for email in emails:
            if User.objects.filter(email=email).exists():
                membership, created = Membership.objects.get_or_create(
                    proposal=self,
                    user=User.objects.get(email=email),
                    role=role
                )
                if created:
                    membership.send_notification()
            else:
                proposal_invite, created = ProposalInvite.objects.get_or_create(
                    proposal=self,
                    role=role,
                    email=email
                )
                proposal_invite.send_invitation()

        logger.info('Users added to proposal {0}: {1}'.format(self, emails))

    def __str__(self):
        return self.id


TimeAllocationKey = namedtuple('TimeAllocationKey', ['semester', 'telescope_class', 'instrument_name'])


class TimeAllocation(models.Model):
    TELESCOPE_CLASSES = (
        ('2m0', '2m0'),
        ('1m0', '1m0'),
        ('0m8', '0m8'),
        ('0m4', '0m4'),
    )

    INSTRUMENT_NAMES = (
        ('0M4-SCICAM-SBIG', '0M4-SCICAM-SBIG'),
        ('0M8-NRES-SCICAM', '0M8-NRES-SCICAM'),
        ('0M8-SCICAM-SBIG', '0M8-SCICAM-SBIG'),
        ('1M0-NRES-SCICAM', '1M0-NRES-SCICAM'),
        ('1M0-SCICAM-SINISTRO', '1M0-SCICAM-SINISTRO'),
        ('1M0-SCICAM-SBIG', '1M0-SCICAM-SBIG'),
        ('1M0-NRES-COMMISSIONING', '1M0-NRES-COMMISSIONING'),
        ('2M0-FLOYDS-SCICAM', '2M0-FLOYDS-SCICAM'),
        ('2M0-SCICAM-SPECTRAL', '2M0-SCICAM-SPECTRAL')
    )

    std_allocation = models.FloatField(default=0)
    std_time_used = models.FloatField(default=0)
    ipp_limit = models.FloatField(default=0)
    ipp_time_available = models.FloatField(default=0)
    too_allocation = models.FloatField(default=0)
    too_time_used = models.FloatField(default=0)
    semester = models.ForeignKey(Semester)
    proposal = models.ForeignKey(Proposal)
    telescope_class = models.CharField(max_length=20, choices=TELESCOPE_CLASSES)
    instrument_name = models.CharField(max_length=200, choices=INSTRUMENT_NAMES)

    def __str__(self):
        return 'Timeallocation for {0}-{1}'.format(self.proposal, self.semester)


class Membership(models.Model):
    PI = 'PI'
    CI = 'CI'
    ROLE_CHOICES = (
        (PI, 'Pricipal Investigator'),
        (CI, 'Co-Investigator')
    )

    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ('user', 'proposal')

    def send_notification(self):
        subject = _('You have been added to a proposal at LCO.global')
        message = render_to_string(
            'proposals/added.txt',
            {
                'proposal': self.proposal,
                'user': self.user,
            }
        )
        send_mail.delay(subject, message, 'portal@lco.glboal', [self.user.email])

    def __str__(self):
        return '{0} {1} of {2}'.format(self.user, self.role, self.proposal)


class ProposalInvite(models.Model):
    proposal = models.ForeignKey(Proposal)
    role = models.CharField(max_length=5, choices=Membership.ROLE_CHOICES)
    email = models.EmailField()
    sent = models.DateTimeField(null=True)
    used = models.DateTimeField(null=True)

    def __str__(self):
        return 'Invitation for {} token {}'.format(self.proposal, self.email)

    def accept(self, user):
        Membership.objects.create(
            proposal=self.proposal,
            role=self.role,
            user=user,
        )
        self.used = timezone.now()
        self.save()

    def send_invitation(self):
        subject = _('You have been added to a proposal at LCO.global')
        message = render_to_string(
            'proposals/invitation.txt',
            {
                'proposal': self.proposal,
                'url': reverse('registration_register')
            }
        )

        send_mail.delay(subject, message, 'portal@lco.glboal', [self.email])
        self.sent = timezone.now()
        self.save()


class ProposalNotification(models.Model):
    proposal = models.ForeignKey(Proposal)
    user = models.ForeignKey(User)

    def __str__(self):
        return '{} - {}'.format(self.proposal, self.user)

    class Meta:
        unique_together = ('proposal', 'user')
