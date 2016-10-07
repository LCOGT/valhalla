from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.functional import cached_property
from django.core.validators import MinValueValidator, MaxValueValidator
import requests
from math import ceil

from valhalla.proposals.models import Proposal
from valhalla.common.configdb import ConfigDB
from valhalla.common.instruments import get_num_filter_changes, get_num_mol_changes


class UserRequest(models.Model):
    STATE_CHOICES = (
        ('PENDING', 'PENDING'),
        ('SCHEDULED', 'SCHEDULED'),
        ('COMPLETED', 'COMPLETED'),
        ('PARTIALLY_COMPLETE', 'PARTIALLY COMPLETE'),
        ('NOT_ATTEMPTED', 'NOT ATTEMPTED'),
        ('CANCELED', 'CANCELED'),
    )

    OPERATOR_CHOICES = (
        ('AND', 'AND'),
        ('SINGLE', 'SINGLE'),
        ('MANY', 'MANY'),
    )

    submitter = models.ForeignKey(User)
    proposal = models.ForeignKey(Proposal)
    group_id = models.CharField(max_length=50, default='', blank=True)
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES)
    ipp_value = models.FloatField(default=1.0, validators=[MinValueValidator(0.5)])
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    state = models.CharField(max_length=40, choices=STATE_CHOICES, default=STATE_CHOICES[0][0])
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return self.get_id_display()

    def get_id_display(self):
        return str(self.id).zfill(10)

    @property
    def blocks(self):
        blocks = []
        for request in self.requests_set.all():
            blocks += request.blocks
        return blocks

    @property
    def frames(self):
        frames = []
        for request in self.requests_set.all():
            frames += request.frames
        return frames


class Request(models.Model):
    STATE_CHOICES = (
        ('PENDING', 'PENDING'),
        ('SCHEDULED', 'SCHEDULED'),
        ('COMPLETED', 'COMPLETED'),
        ('PARTIALLY_COMPLETE', 'PARTIALLY COMPLETE'),
        ('NOT_ATTEMPTED', 'NOT ATTEMPTED'),
    )

    OBSERVATION_TYPES = (
        ('NORMAL', 'NORMAL'),
        ('TARGET_OF_OPPORTUNITY', 'TARGET_OF_OPPORTUNITY'),
    )

    user_request = models.ForeignKey(UserRequest)
    observation_note = models.CharField(max_length=255, default='', blank=True)
    state = models.CharField(max_length=40, choices=STATE_CHOICES, default=STATE_CHOICES[0][0])
    modified = models.DateTimeField(auto_now=True, db_index=True)
    observation_type = models.CharField(max_length=40, choices=OBSERVATION_TYPES, default=OBSERVATION_TYPES[0][0])

    # Counter for number of failed transitions
    fail_count = models.PositiveIntegerField(default=0)
    # Counter for number of times this has been scheduled
    scheduled_count = models.PositiveIntegerField(default=0)

    # Timestamp variables
    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.get_id_display()

    def get_id_display(self):
        return str(self.id).zfill(10)

    @cached_property
    def blocks(self):
        response = requests.get(
            'http://{0}:12000/pond/pond/block/request/{1}.json'.format(
                settings.POND_HOST, self.id
            )
        )
        response.raise_for_status()
        return response.json()

    @cached_property
    def frames(self):
        headers = {'Authorization': 'Token {}'.format(settings.ARCHIVE_API_TOKEN)}
        response = requests.get(
            '{0}frames/?REQNUM={1}&limit=1000'.format(settings.ARCHIVE_API, self.id),
            headers=headers
        )
        response.raise_for_status()
        return response.json()['results']

    @cached_property
    def duration(self):
        # calculate the total time needed by the request, based on its instrument and exposures
        configdb = ConfigDB()
        instrument_type = self.molecule_set.first().instrument_name
        request_overheads = configdb.get_request_overheads(instrument_type)
        duration = sum([m.duration for m in self.molecule_set.all()])
        if configdb.is_spectrograph(instrument_type):
            duration += get_num_mol_changes(self.molecule_set.all()) * request_overheads['config_change_time']

            if self.target.acquire_mode.upper() != 'OFF':
                mol_types = [mol.type.upper() for mol in self.molecule_set.all()]
                # Only add the overhead if we have on-sky targets to acquire
                if 'SPECTRUM' in mol_types or 'STANDARD' in mol_types:
                    duration += request_overheads['acquire_exposure_time'] + request_overheads['acquire_processing_time']

        else:
            duration += get_num_filter_changes(self.molecule_set.all()) * request_overheads['filter_change_time']

        duration += request_overheads['front_padding']
        duration = ceil(duration)

        return duration


class Location(models.Model):
    TELESCOPE_CLASSES = (
        ('2m0', '2m0'),
        ('1m0', '1m0'),
        ('0m8', '0m8'),
        ('0m4', '0m4'),
    )
    request = models.OneToOneField(Request)
    telescope_class = models.CharField(max_length=20, choices=TELESCOPE_CLASSES)
    site = models.CharField(max_length=20, default='', blank=True)
    observatory = models.CharField(max_length=20, default='', blank=True)
    telescope = models.CharField(max_length=20, default='', blank=True)

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

    ACQUIRE_MODES = (
        ('OPTIONAL', 'OPTIONAL'),
        ('ON', 'ON'),
    )

    name = models.CharField(max_length=255)
    request = models.OneToOneField(Request)

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
    proper_motion_ra = models.FloatField(null=True, blank=True)
    proper_motion_dec = models.FloatField(null=True, blank=True)
    epoch = models.FloatField(max_length=20, null=True, blank=True)
    parallax = models.FloatField(null=True, blank=True)

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
                                     validators=[MinValueValidator(0.0),])
    meanlong = models.FloatField(verbose_name='Mean longitude (deg)', null=True, blank=True)
    meananom = models.FloatField(verbose_name='Mean anomoly (deg)', null=True, blank=True,
                                 validators=[MinValueValidator(0.0), MaxValueValidator(360.0)])
    dailymot = models.FloatField(verbose_name='Daily motion (deg)', null=True, blank=True)
    epochofperih = models.FloatField(verbose_name='Epoch of perihelion (MJD)', null=True, blank=True,
                                     validators=[MinValueValidator(10000), MaxValueValidator(100000)])

    # Spectrograph parameters
    acquire_mode = models.CharField(max_length=50, choices=ACQUIRE_MODES, default=ACQUIRE_MODES[0][0])
    rot_mode = models.CharField(max_length=50, choices=ROT_MODES, default='', blank=True)
    rot_angle = models.FloatField(default=0.0, blank=True)


class Window(models.Model):
    request = models.ForeignKey(Request)
    start = models.DateTimeField()
    end = models.DateTimeField()


class Molecule(models.Model):
    PER_MOLECULE_GAP = 5.0             # in-between molecule gap - shared for all instruments
    PER_MOLECULE_STARTUP_TIME = 11.0   # per-molecule startup time, which encompasses filter changes
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

    request = models.ForeignKey(Request)

    # The type of molecule being requested.
    # Valid types are: DARK, BIAS, EXPOSE, SKY_FLAT, HARTMANN, STANDARD,
    #                  ARC, LAMP_FLAT, SPECTRUM, AUTO_FOCUS, ZERO_POINTING
    type = models.CharField(max_length=50, choices=MOLECULE_TYPES, default=MOLECULE_TYPES[0][0])

    # Place-holder for future functionality, allowing arguments to be
    # passed along with a molecule
    args = models.TextField(default='', blank=True)
    # TODO we don't know if this is necessary or if it is used
    priority = models.IntegerField(default=500)

    # Autoguider
    ag_name = models.CharField(max_length=50, default='', blank=True)
    ag_mode = models.CharField(max_length=50, choices=AG_MODES, default=AG_MODES[0][0])
    ag_filter = models.CharField(max_length=50, default='', blank=True)
    ag_exp_time = models.FloatField(default=10.0, blank=True)

    # Instrument
    instrument_name = models.CharField(max_length=255)
    filter = models.CharField(max_length=255, blank=True, default='')
    readout_mode = models.CharField(max_length=50, default='', blank=True)

    # Spectrograph
    spectra_lamp = models.CharField(max_length=50, default='', blank=True)
    spectra_slit = models.CharField(max_length=50, default='', blank=True)
    acquire_mode = models.CharField(max_length=50, choices=ACQUIRE_MODES, default=ACQUIRE_MODES[0][0], blank=True)
    acquire_radius_arcsec = models.FloatField(default=0.0, blank=True)

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
    defocus = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-10.0), MaxValueValidator(40.0)])

    @cached_property
    def duration(self):
        configdb = ConfigDB()
        total_overhead_per_exp = configdb.get_exposure_overhead(self.instrument_name, self.bin_x)
        mol_duration = self.exposure_count * (self.exposure_time + total_overhead_per_exp)
        duration = mol_duration + self.PER_MOLECULE_GAP + self.PER_MOLECULE_STARTUP_TIME

        return duration


class Constraints(models.Model):
    request = models.OneToOneField(Request)
    max_airmass = models.FloatField(default=2.0, validators=[MinValueValidator(1.0), MaxValueValidator(25.0)])
    min_lunar_distance = models.FloatField(default=30.0, validators=[MinValueValidator(0.0), MaxValueValidator(180.0)])
    max_lunar_phase = models.FloatField(null=True, blank=True)
    max_seeing = models.FloatField(null=True, blank=True)
    min_transparency = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Constraints'
