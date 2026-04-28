from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import Button, StateAction, StateView, Wizard


class RegisterHealthProfessionalStart(ModelView):
    'Register Health Professional Start'
    __name__ = 'z_wizard_medics.health_professional.start'

    name = fields.Char('Name')


class RegisterHealthProfessionalWizard(Wizard):
    'Register Health Professional'
    __name__ = 'z_wizard_medics.register_health_professional'

    start = StateView(
        'z_wizard_medics.health_professional.start',
        'z_wizard_medics.register_health_professional_start_view', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_', 'tryton-ok', default=True),
        ])
    create_ = StateAction('health.gnuhealth_action_healthprofessional')

    def _raise_user_error(self, message):
        try:
            raise UserError(gettext(message))
        except Exception:
            raise UserError(message)

    def _validate_start(self):
        start = self.start

        weekdays = [
            start.monday,
            start.tuesday,
            start.wednesday,
            start.thursday,
            start.friday,
            start.saturday,
            start.sunday,
        ]
        if not any(weekdays):
            self._raise_user_error(
                'At least one working day must be selected.')

        if start.time_end <= start.time_start:
            self._raise_user_error(
                'Working hour end must be later than start.')

        if start.appointment_minutes <= 0:
            self._raise_user_error(
                'Appointment minutes must be greater than zero.')

        if start.daily_appointment_quantity <= 0:
            self._raise_user_error(
                'Daily appointment quantity must be greater than zero.')

    def _specialty_ids(self):
        specialty_ids = []
        if self.start.main_specialty:
            specialty_ids.append(self.start.main_specialty.id)

        if self.start.specialties:
            for specialty in self.start.specialties:
                if specialty.id not in specialty_ids:
                    specialty_ids.append(specialty.id)

        return specialty_ids

    def do_create_(self, action):
        self._validate_start()

        pool = Pool()
        Party = pool.get('party.party')
        Employee = pool.get('company.employee')
        HealthProfessional = pool.get('gnuhealth.healthprofessional')
        HealthProfessionalSpecialty = pool.get('gnuhealth.hp_specialty')

        party, = Party.create([{
                    'name': self.start.name,
                    'lastname': self.start.lastname,
                    'gender': self.start.gender,
                    'is_person': True,
                    'is_healthprof': True,
                    }])

        Employee.create([{
                    'party': party.id,
                    'company': self.start.company.id,
                    'cargo': self.start.cargo,
                    }])

        healthprofessional, = HealthProfessional.create([{
                    'name': party.id,
                    'institution': self.start.institution.id,
                    'code': self.start.code,
                    'is_doctor': self.start.is_doctor,
                    'info': self.start.info,
                    'time_start': self.start.time_start,
                    'time_end': self.start.time_end,
                    'appointment_minutes': self.start.appointment_minutes,
                    'monday': self.start.monday,
                    'tuesday': self.start.tuesday,
                    'wednesday': self.start.wednesday,
                    'thursday': self.start.thursday,
                    'friday': self.start.friday,
                    'saturday': self.start.saturday,
                    'sunday': self.start.sunday,
                    'daily_appointment_quantity': self.start.daily_appointment_quantity,
                    }])

        main_hp_specialty = None
        for specialty_id in self._specialty_ids():
            hp_specialty, = HealthProfessionalSpecialty.create([{
                        'name': healthprofessional.id,
                        'specialty': specialty_id,
                        }])
            if specialty_id == self.start.main_specialty.id:
                main_hp_specialty = hp_specialty

        if not main_hp_specialty:
            self._raise_user_error(
                'The main specialty could not be assigned.')

        HealthProfessional.write([healthprofessional], {
                'main_specialty': main_hp_specialty.id,
                })

        data = {'res_id': [healthprofessional.id]}
        action['views'].reverse()
        return action, data
