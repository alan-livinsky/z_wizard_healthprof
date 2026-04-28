from pathlib import Path

from setuptools import setup


MODULE_NAME = "z_wizard_medics"
PACKAGE_ROOT = f"trytond.modules.{MODULE_NAME}"
BASE_DIR = Path(__file__).parent


setup(
    name="trytond-z-wizard-medics",
    version="4.2.0",
    description="Tryton/GNU Health wizard to register health professionals.",
    long_description=(BASE_DIR / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Local customization",
    python_requires=">=3.10,<3.11",
    packages=[
        PACKAGE_ROOT,
        f"{PACKAGE_ROOT}.wizard",
    ],
    package_dir={
        PACKAGE_ROOT: ".",
        f"{PACKAGE_ROOT}.wizard": "wizard",
    },
    package_data={
        PACKAGE_ROOT: [
            "tryton.cfg",
            "view/*.xml",
            "wizard/*.xml",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "trytond>=6.0,<6.1",
        "trytond_company>=6.0,<6.1",
        "gnuhealth==4.2.0",
        "health_appointment_fiuner==4.2.0",
        "health_appointment_screen_fiuner==4.2.0",
        "trytond-z-health-employee-custom>=6.0,<6.1",
    ],
    entry_points={
        "trytond.modules": [
            f"{MODULE_NAME} = {PACKAGE_ROOT}",
        ],
    },
)
