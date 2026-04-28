from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import Button, StateAction, StateView, Wizard


class RegisterHealthProfessionalStart(ModelView):
    'Register Health Professional Start'
    __name__ = 'z_wizard_medics.health_professional.start'

    name = fields.Char('Name', required=True)
    lastname = fields.Char('Family names', required=True)
    gender = fields.Selection([
            (None, ''),
            ('m', 'Male'),
            ('f', 'Female'),
            ('nb', 'Non-binary'),
            ('other', 'Other'),
            ('nd', 'Non disclosed'),
            ('u', 'Unknown'),
            ], 'Gender', required=True, sort=False)

    company = fields.Many2One('company.company', 'Company', required=True)
    cargo = fields.Char('Cargo', required=True)

    institution = fields.Many2One(
        'gnuhealth.institution', 'Institution', required=True)
    code = fields.Char('LICENSE ID')
    is_doctor = fields.Boolean('Is a doctor?',
        help='Check if it is a doctor')
    main_specialty = fields.Many2One(
        'gnuhealth.specialty', 'Main Specialty', required=True)
    specialties = fields.Many2Many(
        'gnuhealth.specialty', None, None, 'Additional Specialties')
    info = fields.Text('Extra info')

    time_start = fields.Time('Hora de Inicio', required=True, format='%H:%M')
    time_end = fields.Time('Hora de Fin', required=True, format='%H:%M')
    appointment_minutes = fields.Integer(
        'Minutos entre entre citas', required=True)
    monday = fields.Boolean('Lunes')
    tuesday = fields.Boolean('Martes')
    wednesday = fields.Boolean('Miercoles')
    thursday = fields.Boolean('Jueves')
    friday = fields.Boolean('Viernes')
    saturday = fields.Boolean('Sabado')
    sunday = fields.Boolean('Domingo')
    daily_appointment_quantity = fields.Integer(
        'Cantidad de turnos por dia', required=True,
        help='Cantidad de turnos a otorgar')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_is_doctor():
        return False

    @staticmethod
    def default_monday():
        return True

    @staticmethod
    def default_friday():
        return True

    @fields.depends('appointment_minutes', 'time_end', 'time_start',
        'daily_appointment_quantity')
    def on_change_with_daily_appointment_quantity(self):
        if (self.appointment_minutes and self.time_end and self.time_start
                and not self.daily_appointment_quantity):
            delta_hours = self.time_end.hour - self.time_start.hour
            delta_minutes = self.time_end.minute - self.time_start.minute
            delta_time = (delta_hours * 60 + delta_minutes) if delta_hours > 0 else 0
            if delta_time > 0:
                return int(delta_time / self.appointment_minutes)
        return self.daily_appointment_quantity

    @fields.depends('daily_appointment_quantity', 'time_end', 'time_start',
        'appointment_minutes')
    def on_change_with_appointment_minutes(self):
        if (self.daily_appointment_quantity and self.time_end and self.time_start
                and not self.appointment_minutes):
            delta_hours = self.time_end.hour - self.time_start.hour
            delta_minutes = self.time_end.minute - self.time_start.minute
            delta_time = (delta_hours * 60 + delta_minutes) if delta_hours > 0 else 0
            if delta_time > 0:
                return int(delta_time / self.daily_appointment_quantity)
        return self.appointment_minutes


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

        specialty_rows = []
        main_hp_specialty = None
        for specialty_id in self._specialty_ids():
            hp_specialty, = HealthProfessionalSpecialty.create([{
                        'name': healthprofessional.id,
                        'specialty': specialty_id,
                        }])
            specialty_rows.append(hp_specialty)
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
