from django.core.management import BaseCommand
from wdipranges.models import IPRange

class Command(BaseCommand):
    help = 'Refreshes the IP ranges from Wikidata'

    def handle(self, *args, **kwargs):
        IPRange.update_from_wikidata()

