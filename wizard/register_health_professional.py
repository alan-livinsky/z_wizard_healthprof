from trytond.exceptions import UserError
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.wizard import Button, StateAction, StateView, Wizard


class RegisterHealthProfessionalStart(ModelView):
    'Inicio de Registro de Profesional de la Salud'
    __name__ = 'z_wizard_healthprof.register_health_professional.start'

    name = fields.Char('Nombre', required=True)
    lastname = fields.Char('Apellidos', required=True)
    idup = fields.Char('IDUP / DNI', required=True)
    cuit = fields.Char('CUIT')
    gender = fields.Selection([
            (None, ''),
            ('m', 'Masculino'),
            ('f', 'Femenino'),
            ('nb', 'No binario'),
            ('other', 'Otro'),
            ('nd', 'No informado'),
            ('u', 'Desconocido'),
            ], 'Genero', required=True, sort=False)

    company = fields.Many2One(
        'company.company', 'Institucion/Empresa contratante', required=True)
    start_date = fields.Date('Fecha de inicio', required=True)
    cargo = fields.Char('Cargo', required=True)

    institution = fields.Many2One(
        'gnuhealth.institution', 'Institucion', required=True)
    code = fields.Char('Matricula')
    is_doctor = fields.Boolean(
        'Es medico?',
        help='Indica si el profesional es medico.')
    main_specialty = fields.Many2One(
        'gnuhealth.specialty', 'Especialidad principal', required=True)
    specialties = fields.Many2Many(
        'gnuhealth.specialty', None, None, 'Especialidades adicionales')
    info = fields.Text('Informacion adicional')

    time_start = fields.Time('Hora de inicio', format='%H:%M')
    time_end = fields.Time('Hora de fin', format='%H:%M')
    appointment_minutes = fields.Integer('Minutos entre citas')
    monday = fields.Boolean('Lunes')
    tuesday = fields.Boolean('Martes')
    wednesday = fields.Boolean('Miercoles')
    thursday = fields.Boolean('Jueves')
    friday = fields.Boolean('Viernes')
    saturday = fields.Boolean('Sabado')
    sunday = fields.Boolean('Domingo')
    daily_appointment_quantity = fields.Integer(
        'Cantidad de turnos por dia',
        help='Cantidad maxima de turnos a otorgar por dia.')

    @staticmethod
    def default_is_doctor():
        return False

    @staticmethod
    def default_institution():
        HealthProfessional = Pool().get('gnuhealth.healthprofessional')
        return HealthProfessional.default_institution()

    def _compute_delta_time(self):
        if self.time_start and self.time_end and self.time_end > self.time_start:
            delta_hours = self.time_end.hour - self.time_start.hour
            delta_minutes = self.time_end.minute - self.time_start.minute
            return delta_hours * 60 + delta_minutes
        return 0

    @fields.depends('appointment_minutes', 'time_end', 'time_start',
        'daily_appointment_quantity')
    def on_change_with_daily_appointment_quantity(self):
        if self.appointment_minutes:
            delta_time = self._compute_delta_time()
            if delta_time > 0:
                return int(delta_time / self.appointment_minutes)
        return self.daily_appointment_quantity

    @fields.depends('daily_appointment_quantity', 'time_end', 'time_start',
        'appointment_minutes')
    def on_change_with_appointment_minutes(self):
        if self.daily_appointment_quantity:
            delta_time = self._compute_delta_time()
            if delta_time > 0:
                return int(delta_time / self.daily_appointment_quantity)
        return self.appointment_minutes

    @fields.depends('appointment_minutes', 'time_end', 'time_start',
        'daily_appointment_quantity')
    def on_change_appointment_minutes(self):
        if self.appointment_minutes:
            self.daily_appointment_quantity = (
                self.on_change_with_daily_appointment_quantity())

    @fields.depends('appointment_minutes', 'time_end', 'time_start',
        'daily_appointment_quantity')
    def on_change_daily_appointment_quantity(self):
        if self.daily_appointment_quantity:
            self.appointment_minutes = self.on_change_with_appointment_minutes()

    @fields.depends('appointment_minutes', 'time_end', 'time_start',
        'daily_appointment_quantity')
    def on_change_time_start(self):
        if self.appointment_minutes:
            self.daily_appointment_quantity = (
                self.on_change_with_daily_appointment_quantity())
        elif self.daily_appointment_quantity:
            self.appointment_minutes = self.on_change_with_appointment_minutes()

    @fields.depends('appointment_minutes', 'time_end', 'time_start',
        'daily_appointment_quantity')
    def on_change_time_end(self):
        if self.appointment_minutes:
            self.daily_appointment_quantity = (
                self.on_change_with_daily_appointment_quantity())
        elif self.daily_appointment_quantity:
            self.appointment_minutes = self.on_change_with_appointment_minutes()


class RegisterHealthProfessionalWizard(Wizard):
    'Registrar Profesional de la Salud'
    __name__ = 'z_wizard_healthprof.register_health_professional'

    start = StateView(
        'z_wizard_healthprof.register_health_professional.start',
        'z_wizard_healthprof.register_health_professional_start_view', [
            Button('Cancelar', 'end', 'tryton-cancel'),
            Button('Crear', 'create_', 'tryton-ok', default=True),
        ])
    create_ = StateAction('health.gnuhealth_action_healthprofessional')

    def _raise_user_error(self, message):
        raise UserError(message)

    def _validate_start(self):
        start = self.start

        if start.cuit and not start.cuit.isdigit():
            self._raise_user_error(
                'El CUIT debe contener solo numeros.')

        weekdays = [
            start.monday,
            start.tuesday,
            start.wednesday,
            start.thursday,
            start.friday,
            start.saturday,
            start.sunday,
        ]
        has_schedule_data = any(weekdays) or any([
            start.time_start,
            start.time_end,
            start.appointment_minutes,
            start.daily_appointment_quantity,
        ])

        if not has_schedule_data:
            return

        if not any(weekdays):
            self._raise_user_error(
                'Debe seleccionar al menos un dia de trabajo.')

        if not start.time_start or not start.time_end:
            self._raise_user_error(
                'Debe completar la hora de inicio y la hora de fin.')

        if start.time_end <= start.time_start:
            self._raise_user_error(
                'La hora de fin debe ser posterior a la hora de inicio.')

        if not start.appointment_minutes:
            self._raise_user_error(
                'Debe completar los minutos entre citas.')

        if start.appointment_minutes <= 0:
            self._raise_user_error(
                'Los minutos entre citas deben ser mayores a cero.')

        if (not start.daily_appointment_quantity and start.appointment_minutes
                and start.time_start and start.time_end):
            start.daily_appointment_quantity = (
                start.on_change_with_daily_appointment_quantity())

        if start.daily_appointment_quantity <= 0:
            self._raise_user_error(
                'La cantidad de turnos por dia debe ser mayor a cero.')

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
        AlternativePersonID = pool.get(
            'gnuhealth.person_alternative_identification')
        fed_country = Party.default_fed_country() or 'XXX'

        party, = Party.create([{
                    'name': self.start.name,
                    'lastname': self.start.lastname,
                    'fed_country': fed_country,
                    'ref': self.start.idup,
                    'gender': self.start.gender,
                    'is_person': True,
                    'is_healthprof': True,
                    'alternative_identification': bool(self.start.cuit),
                    }])

        if self.start.cuit:
            AlternativePersonID.create([{
                        'name': party.id,
                        'code': self.start.cuit,
                        'alternative_id_type': 'cuit',
                        }])

        Employee.create([{
                    'party': party.id,
                    'company': self.start.company.id,
                    'start_date': self.start.start_date,
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
                    'daily_appointment_quantity':
                        self.start.daily_appointment_quantity,
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
                'No se pudo asignar la especialidad principal.')

        HealthProfessional.write([healthprofessional], {
                'main_specialty': main_hp_specialty.id,
                })

        data = {'res_id': [healthprofessional.id]}
        action['views'].reverse()
        return action, data
