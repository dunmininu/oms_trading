"""
Celery tasks for distributed strategy execution.
"""

import logging

from celery import shared_task

from apps.oms.models import Instrument
from apps.strategies.grading_services import GradingService
from apps.tenants.models import Tenant

logger = logging.getLogger(__name__)


@shared_task(name="apps.strategies.tasks.scan_all_instruments")
def scan_all_instruments():
    """Distributed task to trigger setup detection for all active instruments."""
    tenants = Tenant.objects.filter(is_active=True)
    instruments = Instrument.objects.filter(is_active=True)

    for tenant in tenants:
        for instrument in instruments:
            # Dispatch individual scan task per instrument/tenant to workers
            scan_instrument_setup.delay(tenant.id, instrument.id)


@shared_task(name="apps.strategies.tasks.scan_instrument_setup")
def scan_instrument_setup(tenant_id, instrument_id):
    """Scan a specific instrument for a tenant."""
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        instrument = Instrument.objects.get(id=instrument_id)

        # This will run ICT + Quant + ML Grading
        grading_result = GradingService.grade_setup(
            instrument, "15_MINUTE", tenant=tenant
        )

        if grading_result["grade"] in ["A+", "B"]:
            logger.info(
                f"SIGNAL FOUND: {tenant.name} - {instrument.symbol} - Grade {grading_result['grade']}"
            )
            # In production, this would trigger trade execution if auto-start is enabled

    except Exception as e:
        logger.error(
            f"Error scanning instrument {instrument_id} for tenant {tenant_id}: {e}"
        )
