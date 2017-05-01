from django.db import models
import netfields
from netaddr import IPNetwork
from SPARQLWrapper import SPARQLWrapper, JSON
from .utils import to_q

class IPRange(models.Model):
    """
    IPv4/v6 range associated to some Qid on Wikidata.
    """
    objects = netfields.NetManager()

    #: The CIDR representation of the range
    cidr = netfields.CidrAddressField(db_index=True)
    #: The number after the slash in the CIDR representation
    level = models.IntegerField(default=0,db_index=True)
    #: The Wikidata QID associated with this range
    qid = models.CharField(max_length=32,db_index=True)

    last_modified = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        """
        Prefills the 'level' field based on the CIDR
        """
        level = kwargs.get('level')
        cidr = kwargs.get('cidr')
        if not level and cidr:
            kwargs['level'] = int(cidr.split('/')[1])
        super(IPRange, self).__init__(*args, **kwargs)

    @classmethod
    def update_from_wikidata(cls, batch_size=512):
        """
        Clears up the stored IP ranges and adds
        fresh ones from Wikidata
        """
        sparql_query = """
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        SELECT ?cidr ?qid WHERE {
        ?qid (wdt:P3761|wdt:P3793) ?cidr }
        """
        sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        # clear up everything
        cls.objects.all().delete()

        instances = []
        for result in results['results']['bindings']:
            qid = to_q(result['qid']['value'])
            cidr = str(IPNetwork(str(result['cidr']['value'])).ipv6())
            instances.append(cls(qid=qid, cidr=cidr))

        # recreate everything
        cls.objects.bulk_create(instances, batch_size=batch_size)


    def __str__(self):
        return "%s -> %s" % (str(self.cidr),self.qid)

    def json(self):
        return {
            'cidr':str(self.cidr),
            'qid':self.qid,
        }

