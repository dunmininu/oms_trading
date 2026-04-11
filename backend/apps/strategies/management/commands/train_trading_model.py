"""
Management command to train the ML trading model.
"""

from django.core.management.base import BaseCommand
<<<<<<< HEAD
from apps.strategies.ml_services import MLStrategyService
from apps.oms.models import Instrument

class Command(BaseCommand):
    help = 'Train ML models for active instruments'
=======

from apps.oms.models import Instrument
from apps.strategies.ml_services import MLStrategyService


class Command(BaseCommand):
    help = "Train ML models for active instruments"
>>>>>>> origin/main

    def handle(self, *args, **options):
        instruments = Instrument.objects.filter(is_active=True)
        if not instruments.exists():
<<<<<<< HEAD
            self.stdout.write(self.style.WARNING("No active instruments found to train models."))
            return
=======
            from django.core.management import call_command

            self.stdout.write(
                self.style.WARNING(
                    "No active instruments found. Auto-seeding default brokers and instruments..."
                )
            )
            call_command("seed_brokers")
            instruments = Instrument.objects.filter(is_active=True)

            if not instruments.exists():
                self.stdout.write(
                    self.style.ERROR("Failed to seed instruments. Cannot train models.")
                )
                return
>>>>>>> origin/main

        for instrument in instruments:
            self.stdout.write(f"Training model for {instrument.symbol}...")
            # Train on 15min data
<<<<<<< HEAD
            MLStrategyService.train_model(instrument, '15_MINUTE')
            self.stdout.write(self.style.SUCCESS(f"Finished training for {instrument.symbol}"))
=======
            MLStrategyService.train_model(instrument, "15_MINUTE")
            self.stdout.write(
                self.style.SUCCESS(f"Finished training for {instrument.symbol}")
            )
>>>>>>> origin/main
