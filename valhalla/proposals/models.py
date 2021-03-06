from django.contrib.auth.models import User
from django.utils.functional import cached_property
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
    def current_semesters(cls, future=False):
        semesters = cls.objects.filter(end__gte=timezone.now())
        if not future:
            semesters = semesters.filter(start__lte=timezone.now())
        return semesters

    @classmethod
    def future_semesters(cls):
        return cls.objects.filter(start__gt=timezone.now())

    def __str__(self):
        return self.id


class TimeAllocationGroup(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=255, blank=True, default='')
    admin = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    one_meter_alloc = models.PositiveIntegerField(default=0, blank=True)
    two_meter_alloc = models.PositiveIntegerField(default=0, blank=True)
    four_meter_alloc = models.PositiveIntegerField(verbose_name='0.4 Meter Alloc', default=0, blank=True)

    def __str__(self):
        return self.id

    def time_requested_for_semester(self, semester):
        allocs = {
            '1m0': 0,
            '2m0': 0,
            '0m4': 0
        }
        for sciapp in self.admin.scienceapplication_set.filter(call__semester=semester, call__proposal_type='COLAB'):
            for k, v in sciapp.time_requested_by_class.items():
                allocs[k] += v

        return allocs


class Proposal(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    active = models.BooleanField(default=True)
    title = models.CharField(max_length=255, default='', blank=True)
    abstract = models.TextField(default='', blank=True)
    tac_priority = models.PositiveIntegerField(default=0)
    tac_rank = models.PositiveIntegerField(default=0)
    tag = models.ForeignKey(TimeAllocationGroup, on_delete=models.CASCADE)
    public = models.BooleanField(default=False)
    non_science = models.BooleanField(default=False)
    users = models.ManyToManyField(User, through='Membership')

    # Admin only notes
    notes = models.TextField(blank=True, default='', help_text='Add notes here. Not visible to users.')

    # Misc
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('title',)

    @cached_property
    def pi(self):
        return self.users.filter(membership__role=Membership.PI).first()

    @cached_property
    def cis(self):
        return self.users.filter(membership__role=Membership.CI)

    @cached_property
    def current_semester(self):
        return self.semester_set.intersection(Semester.current_semesters()).first()

    @cached_property
    def current_allocation(self):
        allocs = {}
        for ta in self.timeallocation_set.filter(semester=self.current_semester):
            allocs[ta.instrument_name.replace('-', '')] = {
                'std': ta.std_allocation,
                'std_used': ta.std_time_used,
                'too': ta.too_allocation,
                'too_used': ta.too_time_used
            }
        return allocs

    @classmethod
    def current_proposals(cls):
        return cls.objects.filter(semester__in=Semester.current_semesters(future=True))

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
        ('0m4', '0m4'),
        ('0m8', '0m8'),
        ('1m0', '1m0'),
        ('2m0', '2m0'),
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
        ('2M0-SCICAM-SPECTRAL', '2M0-SCICAM-SPECTRAL'),
        ('2M0-SCICAM-SBIG', '2M0-SCICAM-SBIG')
    )

    std_allocation = models.FloatField(default=0)
    std_time_used = models.FloatField(default=0)
    ipp_limit = models.FloatField(default=0)
    ipp_time_available = models.FloatField(default=0)
    too_allocation = models.FloatField(default=0, verbose_name='Rapid Response Allocation')
    too_time_used = models.FloatField(default=0, verbose_name='Rapid Response Time Used')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    telescope_class = models.CharField(max_length=20, choices=TELESCOPE_CLASSES)
    instrument_name = models.CharField(max_length=200, choices=INSTRUMENT_NAMES)

    class Meta:
        ordering = ('-semester__id',)

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
    time_limit = models.IntegerField(default=-1)  # seconds, -1 is unlimited

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
        send_mail.delay(subject, message, 'portal@lco.global', [self.user.email])

    def __str__(self):
        return '{0} {1} of {2}'.format(self.user, self.role, self.proposal)

    @property
    def time_limit_hours(self):
        return self.time_limit / 3600


class ProposalInvite(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
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

        send_mail.delay(subject, message, 'portal@lco.global', [self.email])
        self.sent = timezone.now()
        self.save()


class ProposalNotification(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(self.proposal, self.user)

    class Meta:
        unique_together = ('proposal', 'user')
