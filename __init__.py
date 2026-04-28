from trytond.pool import Pool

from . import wizard


def register():
    Pool.register(
        wizard.RegisterHealthProfessionalStart,
        module='z_wizard_medics', type_='model')
    Pool.register(
        wizard.RegisterHealthProfessionalWizard,
        module='z_wizard_medics', type_='wizard')
