from trytond.pool import Pool

from . import health
from . import wizard


def register():
    Pool.register(
        health.AlternativePersonID,
        module='z_wizard_healthprof', type_='model')
    Pool.register(
        wizard.RegisterHealthProfessionalStart,
        module='z_wizard_healthprof', type_='model')
    Pool.register(
        wizard.RegisterHealthProfessionalWizard,
        module='z_wizard_healthprof', type_='wizard')
