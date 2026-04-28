from trytond.model import ModelView, fields
from trytond.wizard import Button, StateView, Wizard


class RegisterHealthProfessionalStart(ModelView):
    'Register Health Professional Start'
    __name__ = 'z_wizard_healthprof.register_health_professional.start'

    name = fields.Char('Name')


class RegisterHealthProfessionalWizard(Wizard):
    'Register Health Professional'
    __name__ = 'z_wizard_healthprof.register_health_professional'

    start = StateView(
        'z_wizard_healthprof.register_health_professional.start',
        'z_wizard_healthprof.register_health_professional_start_view', [
            Button('Close', 'end', 'tryton-cancel', default=True),
        ])
