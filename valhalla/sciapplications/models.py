from django.db import models


class Instrument(models.Model):
    code = models.CharField(max_length=50)

    def __str__(self):
        return self.code


class Call(models.Model):
    PROPOSAL_TYPES = (
        ('SCI', 'Science'),
        ('KEY', 'Key Project'),
        ('NOAC', 'NOAC')
    )
    semestercode = models.CharField(max_length=6)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    callsent = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)
    callurl = models.URLField(blank=True, null=True)
    instruments = models.ManyToManyField(Instrument)
    ptype = models.CharField(max_length=5, choices=PROPOSAL_TYPES)
    active = models.BooleanField(default=True)
    proposalpdfs = models.FileField(upload_to='sciapp/call/', blank=True, null=True)
    eligibility = models.TextField(blank=True, default='')
    eligibility_short = models.TextField(blank=True, default='')

    def __str__(self):
        return '{0} call for {1}'.format(self.ptype, self.semestercode)


class ScienceApplication(models.Model):
    SCI_PROPOSAL = 'SCI'
    DDT_PROPOSAL = 'DDT'
    KEY_PROPOSAL = 'KEY'

    APP_TYPE_CHOICES = (
        (SCI_PROPOSAL, 'Science'),
        (DDT_PROPOSAL, 'Director\'s Discretionary Time'),
        (KEY_PROPOSAL, 'Key Project')
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PORTED', 'Ported')
    )

    MOON_CHOICES = (
        ('EITHER', 'Either'),
        ('BRIGHT', 'Bright'),
        ('DARK', 'Dark'),
    )

    app_type = models.CharField(max_length=50, choices=APP_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    semester = models.ForeignKey(Call)
    abstract = models.TextField(blank=True, default='')
    pi = models.TextField(blank=True, default='')
    coi = models.TextField(blank=True, default='')
    budget_details = models.TextField()
    instruments = models.ManyToManyField(Instrument)
    moon = models.CharField(max_length=50, choices=MOON_CHOICES, default=MOON_CHOICES[0][0])
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    science_case = models.FileField(upload_to='sciapp/sci_case/', blank=True, null=True)
    experimental_design = models.TextField(blank=True, default='')
    experimental_design_file = models.FileField(upload_to='sciapp/tech/', blank=True, null=True)
    related_programs = models.TextField(blank=True, default='')
    past_use = models.TextField(blank=True, default='')
    publications = models.TextField(blank=True, default='')
    final = models.FileField(upload_to='sciapp/final/', blank=True, null=True)
    attachment = models.FileField(upload_to='sciapp/attachment/', blank=True, null=True)

    # DDT Only fields
    science_justification = models.TextField(blank=True, default='')
    ddt_justification = models.TextField(blank=True, default='')

    # Key project only fields
    management = models.TextField(blank=True, default='')
    relevance = models.TextField(blank=True, default='')
    contribution = models.TextField(blank=True, default='')
