from django.utils.translation import ugettext as _


class BaseTargetHelper(object):
    """
    These helper classes take a dictionary representation of a target
    and performs validation specific to the target type Sidereal,
    NonSidereal, Satellite. The dictionary it returns will also only contain
    fields relevant to the specific type. These models should only be used in
    TargetSerializer
    """
    def __init__(self, target):
        self.error_dict = {}
        self._data = {}

        for field in self.fields:
            self._data[field] = target.get(field)

        for field in self.defaults:
            if not target.get(field):
                self._data[field] = self.defaults[field]

        for field in self.required_fields:
            if not self._data.get(field):
                self.error_dict[field] = ['This field is required']

        self.validate()

    def validate(self):
        pass

    def is_valid(self):
        return not bool(self.error_dict)

    @property
    def data(self):
        # Only return data that is not none so model defaults can take effect
        return {k: v for k, v in self._data.items() if v is not None}


class SiderealTargetHelper(BaseTargetHelper):
    def __init__(self, target):
        self.fields = (
            'type', 'name', 'ra', 'dec', 'proper_motion_ra', 'proper_motion_dec', 'parallax',
            'coordinate_system', 'equinox', 'epoch', 'acquire_mode', 'rot_mode', 'rot_angle'
        )

        self.required_fields = ('ra', 'dec')

        self.defaults = {
            'coordinate_system': 'ICRS',
            'equinox': 'J2000',
            'parallax': 0.0,
            'proper_motion_ra': 0.0,
            'proper_motion_dec': 0.0,
            'epoch': 2000.0
        }
        super().__init__(target)


class NonSiderealTargetHelper(BaseTargetHelper):
    def __init__(self, target):
        self.defaults = {}
        self.fields = (
            'type', 'epochofel', 'orbinc', 'longascnode', 'eccentricity', 'scheme'
        )
        if target.get('scheme') == 'ASA_MAJOR_PLANET':
            self.fields += ('longofperih', 'meandist', 'meanlong', 'dailymot')
        elif target.get('scheme') == 'ASA_MINOR_PLANET':
            self.fields += ('argofperih', 'meandist', 'meananom')
        elif target.get('scheme') == 'ASA_COMET':
            self.fields += ('argofperih', 'perihdist', 'epochofperih')
        elif target.get('scheme') == 'JPL_MAJOR_PLANET':
            self.fields += ('argofperih', 'meandist', 'meananom', 'dailymot')
        elif target.get('scheme') == 'JPL_MINOR_PLANET':
            self.fields += ('argofperih', 'perihdist', 'epochofperih')
        elif target.get('scheme') == 'MPC_MINOR_PLANET':
            self.fields += ('argofperih', 'meandist', 'meananom')
        elif target.get('scheme') == 'MPC_COMET':
            self.fields += ('argofperih', 'perihdist', 'epochofperih')

        self.required_fields = self.fields
        super().__init__(target)

    def validate(self):
        ECCENTRICITY_LIMIT = 0.9
        if self.is_valid() and 'COMET' not in self._data['scheme'] and self._data['eccentricity'] > ECCENTRICITY_LIMIT:
            msg = _("Non sidereal pointing of scheme {} requires eccentricity to be lower than {}. ").format(
                self._data['scheme'], ECCENTRICITY_LIMIT
            )
            msg += _("Submit with scheme MPC_COMET to use your eccentricity of {}.").format(
                self._data['eccentricity']
            )
            self.error_dict['scheme'] = msg


class SatelliteTargetHelper(BaseTargetHelper):
    def __init__(self, target):
        self.fields = (
            'type', 'altitude', 'azimuth', 'diff_pitch_rate', 'diff_roll_rate',
            'diff_epoch_rate', 'diff_pitch_acceleration', 'diff_roll_acceleration'
        )
        self.required_fields = self.fields
        self.defaults = {}
        super().__init__(target)
