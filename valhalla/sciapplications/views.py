from django.views.generic.edit import FormView
from django.http import Http404

from valhalla.sciapplications.models import Call
from valhalla.sciapplications.forms import (ScienceProposalAppForm,
                                            DDTProposalAppForm,
                                            KeyProjectAppForm)


class SciApplicationView(FormView):
    template_name = 'sciapplications/create.html'
    success_url = '/'

    def get_form_class(self):
        app_type = self.kwargs['app_type']
        print(app_type)
        if app_type == 'sci':
            return ScienceProposalAppForm
        elif app_type == 'ddt':
            return DDTProposalAppForm
        elif app_type == 'key':
            return KeyProjectAppForm
        else:
            raise Http404

    def get_initial(self):
        semestercode = self.kwargs['semester']
        try:
            semester = Call.objects.get(semestercode=semestercode)
        except Call.DoesNotExist:
            raise Http404

        return {'semester': semester}
