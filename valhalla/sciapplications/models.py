from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from valhalla.proposals.models import (
    Semester, TimeAllocation, Proposal, TimeAllocationGroup, Membership
)


class Instrument(models.Model):
    code = models.CharField(max_length=50)

    def __str__(self):
        return self.code


class Call(models.Model):
    SCI_PROPOSAL = 'SCI'
    DDT_PROPOSAL = 'DDT'
    KEY_PROPOSAL = 'KEY'
    NAOC_PROPOSAL = 'NAOC'

    PROPOSAL_TYPE_CHOICES = (
        (SCI_PROPOSAL, 'Science'),
        (DDT_PROPOSAL, 'Director\'s Discretionary Time'),
        (KEY_PROPOSAL, 'Key Project'),
        (NAOC_PROPOSAL, 'NAOC proposal')
    )

    semester = models.ForeignKey(Semester)
    opens = models.DateTimeField()
    deadline = models.DateTimeField()
    call_url = models.URLField(blank=True, default='')
    instruments = models.ManyToManyField(Instrument)
    proposal_type = models.CharField(max_length=5, choices=PROPOSAL_TYPE_CHOICES)
    eligibility = models.TextField(blank=True, default='')
    eligibility_short = models.TextField(blank=True, default='')

    @classmethod
    def open_calls(cls):
        return cls.objects.filter(opens__lte=timezone.now(), deadline__gte=timezone.now())

    def __str__(self):
        return '{0} call for {1}'.format(self.get_proposal_type_display(), self.semester)


class ScienceApplication(models.Model):
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'
    PORTED = 'PORTED'

    STATUS_CHOICES = (
        (DRAFT, 'Draft'),
        (SUBMITTED, 'Submitted'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (PORTED, 'Ported')
    )

    MOON_CHOICES = (
        ('EITHER', 'Any'),
        ('BRIGHT', 'Bright'),
        ('DARK', 'Dark'),
    )

    title = models.CharField(max_length=200)
    call = models.ForeignKey(Call)
    submitter = models.ForeignKey(User)
    abstract = models.TextField(blank=True, default='')
    pi = models.EmailField(blank=True, default='')
    coi = models.TextField(blank=True, default='')
    budget_details = models.TextField(blank=True, default='', help_text='')
    instruments = models.ManyToManyField(Instrument, blank=True)
    moon = models.CharField(max_length=50, choices=MOON_CHOICES, default=MOON_CHOICES[0][0], blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    science_case = models.TextField(blank=True, default='')
    science_case_file = models.FileField(upload_to='sciapp/sci_case/', blank=True, null=True)
    experimental_design = models.TextField(blank=True, default='')
    experimental_design_file = models.FileField(upload_to='sciapp/tech/', blank=True, null=True)
    related_programs = models.TextField(blank=True, default='')
    past_use = models.TextField(blank=True, default='')
    publications = models.TextField(blank=True, default='')
    proposal = models.ForeignKey(Proposal, null=True, blank=True)
    tac_rank = models.PositiveIntegerField(default=0)
    tac_priority = models.PositiveIntegerField(default=0)

    # DDT Only fields
    science_justification = models.TextField(blank=True, default='')
    ddt_justification = models.TextField(blank=True, default='')

    # Key project only fields
    management = models.TextField(blank=True, default='')
    relevance = models.TextField(blank=True, default='')
    contribution = models.TextField(blank=True, default='')

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.title

    @property
    def proposal_code(self):
        proposal_type_to_name = {
            'SCI': 'LCOGT',
            'KEY': 'KEY',
            'DDT': 'DDT',
            'NAOC': 'NAOC'
        }
        return '{0}{1}-{2}'.format(
            proposal_type_to_name[self.call.proposal_type], self.call.semester, str(self.tac_rank).zfill(3)
        )

    def convert_to_proposal(self):
        # Create the objects we need
        proposal = Proposal.objects.create(
            id=self.proposal_code,
            title=self.title,
            abstract=self.abstract,
            tac_priority=self.tac_priority,
            tac_rank=self.tac_rank,
            active=False,
            tag=TimeAllocationGroup.objects.get_or_create(id='LCOGT')[0],
        )

        for tr in self.timerequest_set.filter(approved=True):
            TimeAllocation.objects.create(
                std_allocation=tr.std_time,
                too_allocation=tr.too_time,
                telescope_class=tr.telescope_class,
                semester=self.call.semester,
                proposal=proposal
            )

        # Send invitations if necessary
        if self.pi:
            proposal.add_users([self.pi], Membership.PI)
        else:
            Membership.objects.create(proposal=proposal, user=self.submitter, role=Membership.PI)

        cis = [c for c in self.coi.replace(' ', '').split(',') if c]
        proposal.add_users(cis, Membership.CI)

        self.proposal = proposal
        self.status = ScienceApplication.PORTED
        self.save()
        return proposal


class TimeRequest(models.Model):
    science_application = models.ForeignKey(ScienceApplication)
    telescope_class = models.CharField(max_length=20, choices=TimeAllocation.TELESCOPE_CLASSES)
    std_time = models.PositiveIntegerField(default=0, blank=True)
    too_time = models.PositiveIntegerField(default=0, blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return '{} {} TimeRequest'.format(self.science_application, self.telescope_class)
