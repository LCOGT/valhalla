from rest_framework.metadata import BaseMetadata


class RequestMetadata(BaseMetadata):
    def determine_metadata(self, request, view):
        return {
            'units': {
                'requests': {
                    'blocks': {
                        'molecules': {
                            'exp_time': 'seconds',
                            'ag_exp_time': 'seconds',
                            'defocus': 'milimeters',
                        }
                    }
                },
                'targets': {
                    'ra': 'degrees',
                    'dec': 'degrees',
                    'proper_motion_ra': 'miliarcseconds/year with cos(dec) included',
                    'proper_motion_dec': 'miliarcseconds/year',
                }
            }
        }
