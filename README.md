# z_wizard_medics

Local Tryton/GNU Health module that adds a wizard to register health
professionals.

## Requirements

- Python 3.10
- trytond 6.0
- GNU Health 4.2

## Local installation

Install the local custom dependency first if it is not already available in
your environment:

```bash
pip install ../z_health_employee_custom
```

Then install from the module root:

```bash
pip install .
```

For editable local development:

```bash
pip install -e .
```

This package also expects GNU Health 4.2 base modules and the local
`health_appointment_fiuner` and `health_appointment_screen_fiuner` modules to
already be installed in the same Python environment.
