"""
Management command to train the ML trading model.
"""

from django.core.management.base import BaseCommand
from apps.strategies.ml_services import MLStrategyService
from apps.oms.models import Instrument

class Command(BaseCommand):
    help = 'Train ML models for active instruments'

    def handle(self, *args, **options):
        instruments = Instrument.objects.filter(is_active=True)
        if not instruments.exists():
            self.stdout.write(self.style.WARNING("No active instruments found to train models."))
            return

        for instrument in instruments:
            self.stdout.write(f"Training model for {instrument.symbol}...")
            # Train on 15min data
            MLStrategyService.train_model(instrument, '15_MINUTE')
            self.stdout.write(self.style.SUCCESS(f"Finished training for {instrument.symbol}"))
