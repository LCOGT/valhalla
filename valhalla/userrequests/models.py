from django.db import models
from django.contrib.auth.models import User
from django.utils.functional import cached_property
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings
from django.forms.models import model_to_dict
import requests
import logging

from valhalla.proposals.models import Proposal, TimeAllocationKey
from valhalla.userrequests.external_serializers import BlockSerializer
from valhalla.common.rise_set_utils import get_rise_set_target
from valhalla.userrequests.duration_utils import (get_request_duration, get_molecule_duration, get_total_duration_dict,
                                                  get_semester_in)

logger = logging.getLogger(__name__)


class UserRequest(models.Model):
    NORMAL = 'NORMAL'
    TOO = 'TARGET_OF_OPPORTUNITY'

    STATE_CHOICES = (
        ('PENDING', 'PENDING'),
        ('SCHEDULED', 'SCHEDULED'),
        ('COMPLETED', 'COMPLETED'),
        ('WINDOW_EXPIRED', 'WINDOW_EXPIRED'),
        ('CANCELED', 'CANCELED'),
    )

    OPERATOR_CHOICES = (
        ('AND', 'AND'),
        ('SINGLE', 'SINGLE'),
        ('MANY', 'MANY'),
    )

    OBSERVATION_TYPES = (
        ('NORMAL', NORMAL),
        ('TARGET_OF_OPPORTUNITY', TOO),
    )

    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    group_id = models.CharField(max_length=50)
    observation_type = models.CharField(max_length=40, choices=OBSERVATION_TYPES)
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES)
    ipp_value = models.FloatField(validators=[MinValueValidator(0.5)])
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    state = models.CharField(max_length=40, choices=STATE_CHOICES, default=STATE_CHOICES[0][0])
    modified = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.get_id_display()

    def get_id_display(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse('userrequests:detail', kwargs={'pk': self.pk})

    @property
    def as_dict(self):
        ret_dict = model_to_dict(self)
        ret_dict['requests'] = [r.as_dict for r in self.requests.all()]
        return ret_dict

    @property
    def min_window_time(self):
        return min([request.min_window_time for request in self.requests.all()])

    @property
    def max_window_time(self):
        return max([request.max_window_time for request in self.requests.all()])

    @property
    def timeallocations(self):
        return self.proposal.timeallocation_set.filter(
            semester__start__lte=self.min_window_time,
            semester__end__gte=self.max_window_time,
        )

    @property
    def total_duration(self):
        cached_duration = cache.get('userrequest_duration_{}'.format(self.id))
        if not cached_duration:
            duration = get_total_duration_dict(self.as_dict)
            cache.set('userrequest_duration_{}'.format(self.id), duration, 86400 * 30 * 6)
            return duration
        else:
            return cached_duration


class Request(models.Model):
    STATE_CHOICES = (
        ('PENDING', 'PENDING'),
        ('SCHEDULED', 'SCHEDULED'),
        ('COMPLETED', 'COMPLETED'),
        ('WINDOW_EXPIRED', 'WINDOW_EXPIRED'),
        ('CANCELED', 'CANCELED'),
    )

    user_request = models.ForeignKey(UserRequest, related_name='requests', on_delete=models.CASCADE)
    observation_note = models.CharField(max_length=255, default='', blank=True)
    state = models.CharField(max_length=40, choices=STATE_CHOICES, default=STATE_CHOICES[0][0])
    modified = models.DateTimeField(auto_now=True, db_index=True)

    # Counter for number of failed transitions
    fail_count = models.PositiveIntegerField(default=0)
    # Counter for number of times this has been scheduled
    scheduled_count = models.PositiveIntegerField(default=0)

    # Timestamp variables
    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(null=True, blank=True)

    # Minimum completable block threshold (percentage, 0-100)
    acceptability_threshold = models.FloatField(default=90.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.get_id_display()

    def get_id_display(self):
        return str(self.id)

    @property
    def as_dict(self):
        ret_dict = model_to_dict(self)
        ret_dict['target'] = self.target.as_dict
        ret_dict['molecules'] = [m.as_dict for m in self.molecules.all()]
        ret_dict['location'] = self.location.as_dict
        ret_dict['constraints'] = self.constraints.as_dict
        ret_dict['windows'] = [w.as_dict for w in self.windows.all()]
        return ret_dict

    @cached_property
    def duration(self):
        cached_duration = cache.get('request_duration_{}'.format(self.id))
        if not cached_duration:
            duration = get_request_duration(self.as_dict)
            cache.set('request_duration_{}'.format(self.id), duration, 86400 * 30 * 6)
            return duration
        else:
            return cached_duration

    @property
    def min_window_time(self):
        return min([window.start for window in self.windows.all()])

    @property
    def max_window_time(self):
        return max([window.end for window in self.windows.all()])

    @property
    def semester(self):
        return get_semester_in(self.min_window_time, self.max_window_time)

    @property
    def time_allocation_key(self):
        return TimeAllocationKey(self.semester.id, self.location.telescope_class, self.molecules.first().instrument_name)

    @property
    def timeallocation(self):
        return self.user_request.proposal.timeallocation_set.get(
            semester__start__lte=self.min_window_time,
            semester__end__gte=self.max_window_time,
            telescope_class=self.location.telescope_class,
            instrument_name=self.molecules.first().instrument_name
        )

    @cached_property
    def blocks(self):
        try:
            response = requests.get(
                '{0}/pond/pond/block/request/{1}.json'.format(
                    settings.POND_URL, self.get_id_display().zfill(10)  # the pond hardcodes 0 padded strings... awesome
                )
            )
            response.raise_for_status()
            return BlockSerializer(response.json(), many=True).data
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            logger.error('Could not connect to the pond.')
            return BlockSerializer([], many=True).data


class Location(models.Model):
    TELESCOPE_CLASSES = (
        ('2m0', '2m0'),
        ('1m0', '1m0'),
        ('0m8', '0m8'),
        ('0m4', '0m4'),
    )
    request = models.OneToOneField(Request, on_delete=models.CASCADE)
    telescope_class = models.CharField(max_length=20, choices=TELESCOPE_CLASSES)
    site = models.CharField(max_length=20, default='', blank=True)
    observatory = models.CharField(max_length=20, default='', blank=True)
    telescope = models.CharField(max_length=20, default='', blank=True)

    class Meta:
        ordering = ('id',)

    @property
    def as_dict(self):
        return model_to_dict(self)

    def __str__(self):
        return '{}.{}.{}'.format(self.site, self.observatory, self.telescope)


class Target(models.Model):
    ORBITAL_ELEMENT_SCHEMES = (
        ('ASA_MAJOR_PLANET', 'ASA_MAJOR_PLANET'),
        ('ASA_MINOR_PLANET', 'ASA_MINOR_PLANET'),
        ('ASA_COMET', 'ASA_COMET'),
        ('JPL_MAJOR_PLANET', 'JPL_MAJOR_PLANET'),
        ('JPL_MINOR_PLANET', 'JPL_MINOR_PLANET'),
        ('MPC_MINOR_PLANET', 'MPC_MINOR_PLANET'),
        ('MPC_COMET', 'MPC_COMET'),
    )

    POINTING_TYPES = (
        ('SIDEREAL', 'SIDEREAL'),
        ('NON_SIDEREAL', 'NON_SIDEREAL'),
        ('STATIC', 'STATIC'),
        ('SATELLITE', 'SATELLITE'),
    )

    ROT_MODES = (
        ('SKY', 'SKY'),
        ('FLOAT', 'FLOAT'),
        ('VERTICAL', 'VERTICAL'),
        ('VFLOAT', 'VFLOAT'),
    )

    name = models.CharField(max_length=50)
    request = models.OneToOneField(Request, on_delete=models.CASCADE)

    type = models.CharField(max_length=255, choices=POINTING_TYPES)

    # Coordinate modes
    roll = models.FloatField(null=True, blank=True)
    pitch = models.FloatField(null=True, blank=True)
    hour_angle = models.FloatField(null=True, blank=True)
    ra = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0), MaxValueValidator(360.0)])
    dec = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    altitude = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0), MaxValueValidator(90.0)])
    azimuth = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0), MaxValueValidator(360.0)])

    # Pointing details
    coordinate_system = models.CharField(max_length=255, default='', blank=True)
    equinox = models.CharField(max_length=20, default='', blank=True)
    proper_motion_ra = models.FloatField(null=True, blank=True, validators=[MaxValueValidator(20000)])
    proper_motion_dec = models.FloatField(null=True, blank=True, validators=[MaxValueValidator(20000)])
    epoch = models.FloatField(max_length=20, null=True, blank=True, validators=[MaxValueValidator(2100)])
    parallax = models.FloatField(null=True, blank=True, validators=[MaxValueValidator(2000)])

    # Nonsidereal rate
    diff_pitch_rate = models.FloatField(verbose_name='Differential Pitch Rate (arcsec/s)', null=True, blank=True)
    diff_roll_rate = models.FloatField(verbose_name='Differential Roll Rate  (arcsec/s)', null=True, blank=True)
    diff_epoch_rate = models.FloatField(verbose_name='Reference time for non-sidereal motion (MJD)', null=True,
                                        blank=True)

    # Satellite Fields
    diff_pitch_acceleration = models.FloatField(verbose_name='Differential Pitch Acceleration (arcsec/s^2)', null=True,
                                                blank=True)
    diff_roll_acceleration = models.FloatField(verbose_name='Differential Role Acceleration (arcsec/s^2)', null=True,
                                               blank=True)

    # Orbital elements
    scheme = models.CharField(verbose_name='Orbital Element Scheme', max_length=50, choices=ORBITAL_ELEMENT_SCHEMES,
                              default='', blank=True)
    epochofel = models.FloatField(verbose_name='Epoch of elements (MJD)', null=True, blank=True,
                                  validators=[MinValueValidator(10000), MaxValueValidator(100000)])
    orbinc = models.FloatField(verbose_name='Orbital inclination (deg)', null=True, blank=True,
                               validators=[MinValueValidator(0.0), MaxValueValidator(180.0)])
    longascnode = models.FloatField(verbose_name='Longitude of ascending node (deg)', null=True, blank=True,
                                    validators=[MinValueValidator(0.0), MaxValueValidator(360.0)])
    longofperih = models.FloatField(verbose_name='Longitude of perihelion (deg)', null=True, blank=True,
                                    validators=[MinValueValidator(0.0), MaxValueValidator(360.0)])
    argofperih = models.FloatField(verbose_name='Argument of perihelion (deg)', null=True, blank=True,
                                   validators=[MinValueValidator(0.0), MaxValueValidator(360.0)])
    meandist = models.FloatField(verbose_name='Mean distance (AU)', null=True, blank=True)
    perihdist = models.FloatField(verbose_name='Perihelion distance (AU)', null=True, blank=True)
    eccentricity = models.FloatField(verbose_name='Eccentricity', null=True, blank=True,
                                     validators=[MinValueValidator(0.0)])
    meanlong = models.FloatField(verbose_name='Mean longitude (deg)', null=True, blank=True)
    meananom = models.FloatField(verbose_name='Mean anomaly (deg)', null=True, blank=True,
                                 validators=[MinValueValidator(0.0), MaxValueValidator(360.0)])
    dailymot = models.FloatField(verbose_name='Daily motion (deg)', null=True, blank=True)
    epochofperih = models.FloatField(verbose_name='Epoch of perihelion (MJD)', null=True, blank=True,
                                     validators=[MinValueValidator(10000), MaxValueValidator(100000)])

    # Spectrograph parameters
    rot_mode = models.CharField(max_length=50, choices=ROT_MODES, default='', blank=True)
    rot_angle = models.FloatField(default=0.0, blank=True)
    vmag = models.FloatField(null=True, blank=True)
    radvel = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return 'Target {}: {} type'.format(self.id, self.type)

    @property
    def as_dict(self):
        return model_to_dict(self)

    @property
    def rise_set_target(self):
        return get_rise_set_target(self.as_dict)


class Window(models.Model):
    request = models.ForeignKey(Request, related_name='windows', on_delete=models.CASCADE)
    start = models.DateTimeField(db_index=True)
    end = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ('id',)

    @property
    def as_dict(self):
        return model_to_dict(self)

    def __str__(self):
        return 'Window {}: {} to {}'.format(self.id, self.start, self.end)


class Molecule(models.Model):
    # These are filled in from the molecule types possible in requestdb.
    # There are more molecule types that the pond will accept but scheduler will not.
    MOLECULE_TYPES = (
        ('EXPOSE', 'EXPOSE'),
        ('SKY_FLAT', 'SKY_FLAT'),
        ('STANDARD', 'STANDARD'),
        ('ARC', 'ARC'),
        ('LAMP_FLAT', 'LAMP_FLAT'),
        ('SPECTRUM', 'SPECTRUM'),
        ('AUTO_FOCUS', 'AUTO_FOCUS'),
        ('TRIPLE', 'TRIPLE'),
        ('NRES_TEST', 'NRES_TEST'),
        ('NRES_SPECTRUM', 'NRES_SPECTRUM'),
        ('NRES_EXPOSE', 'NRES_EXPOSE'),
        ('ENGINEERING', 'ENGINEERING')
    )

    AG_MODES = (
        ('OPTIONAL', 'OPTIONAL'),
        ('ON', 'ON'),
        ('OFF', 'OFF'),
    )

    ACQUIRE_MODES = (
        ('OFF', 'OFF'),
        ('WCS', 'WCS'),
        ('BRIGHTEST', 'BRIGHTEST'),
    )

    request = models.ForeignKey(Request, related_name='molecules', on_delete=models.CASCADE)

    # The type of molecule being requested.
    # Valid types are in MOLECULE_TYPES
    type = models.CharField(max_length=50, choices=MOLECULE_TYPES)

    # Place-holder for future functionality, allowing arguments to be
    # passed along with a molecule
    args = models.TextField(default='', blank=True)
    # Used by the pond for ordering the molecules
    priority = models.IntegerField(default=500)

    # Autoguider
    ag_name = models.CharField(max_length=50, default='', blank=True)
    ag_mode = models.CharField(max_length=50, choices=AG_MODES, default=AG_MODES[0][0])
    ag_filter = models.CharField(max_length=50, default='', blank=True)
    ag_exp_time = models.FloatField(default=10.0, blank=True)
    ag_strategy = models.CharField(max_length=55, default='', blank=True)

    # Instrument
    instrument_name = models.CharField(max_length=255)
    filter = models.CharField(max_length=255, blank=True, default='')
    readout_mode = models.CharField(max_length=50, default='', blank=True)

    # Spectrograph
    spectra_lamp = models.CharField(max_length=50, default='', blank=True)
    spectra_slit = models.CharField(max_length=50, default='', blank=True)
    acquire_mode = models.CharField(max_length=50, choices=ACQUIRE_MODES, default=ACQUIRE_MODES[0][0], blank=True)
    acquire_radius_arcsec = models.FloatField(default=0.0, blank=True)
    acquire_strategy = models.CharField(max_length=55, default='', blank=True)
    expmeter_mode = models.CharField(max_length=12, default='OFF', blank=True)
    expmeter_snr = models.FloatField(null=True, blank=True)

    # Exposure
    exposure_time = models.FloatField(validators=[MinValueValidator(0)])
    exposure_count = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    # Binning
    bin_x = models.PositiveSmallIntegerField(default=1, blank=True)
    bin_y = models.PositiveSmallIntegerField(default=1, blank=True)

    # Subframe
    sub_x1 = models.PositiveIntegerField(null=True, blank=True)  # Sub Frame X start pixel
    sub_x2 = models.PositiveIntegerField(null=True, blank=True)  # Sub Frame X end pixel
    sub_y1 = models.PositiveIntegerField(null=True, blank=True)  # Sub Frame Y start pixel
    sub_y2 = models.PositiveIntegerField(null=True, blank=True)  # Sub Frame Y end pixel

    # Other options
    defocus = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-3.0), MaxValueValidator(3.0)])

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return 'Molecule {0}: {1} type, {2} instrument, {3} exposures @ {4}s'.format(
            self.id, self.type, self.instrument_name, self.exposure_count, self.exposure_time
        )

    @property
    def as_dict(self):
        return model_to_dict(self)

    @cached_property
    def duration(self):
        return get_molecule_duration(self.as_dict)


class Constraints(models.Model):
    request = models.OneToOneField(Request, on_delete=models.CASCADE)
    max_airmass = models.FloatField(default=1.6, validators=[MinValueValidator(1.0), MaxValueValidator(25.0)])
    min_lunar_distance = models.FloatField(default=30.0, validators=[MinValueValidator(0.0), MaxValueValidator(180.0)])
    max_lunar_phase = models.FloatField(null=True, blank=True)
    max_seeing = models.FloatField(null=True, blank=True)
    min_transparency = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ('id',)
        verbose_name_plural = 'Constraints'

    @property
    def as_dict(self):
        return model_to_dict(self)

    def __str__(self):
        return 'Constraints {}: {} max airmass, {} min_lunar_distance'.format(self.id, self.max_airmass,
                                                                              self.min_lunar_distance)


class DraftUserRequest(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-modified']
        unique_together = ('author', 'proposal', 'title')

    def __str__(self):
        return 'Draft request by: {} for proposal: {}'.format(self.author, self.proposal)
