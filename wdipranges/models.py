from django.db import models
import netfields
from netaddr import IPNetwork
from SPARQLWrapper import SPARQLWrapper, JSON
from .utils import to_q
import re
from unidecode import unidecode

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
    #: A short label for this entity
    label = models.CharField(max_length=512, default='')
    #: A list of comma-separated types (Qids) for this entity
    types_comma = models.CharField(max_length=512, default='')

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
        SELECT ?cidr ?qid ?qidLabel (GROUP_CONCAT(DISTINCT ?type; separator=",")
        AS ?types) WHERE {
        ?qid (wdt:P3761|wdt:P3793) ?cidr ;
            wdt:P31 ?type.
        SERVICE wikibase:label { bd:serviceParam wikibase:language
        "en,fr,de,es,nl" }
        }
        GROUP BY ?cidr ?qid ?qidLabel
        ORDER BY ?qid
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
            label = result['qidLabel'].get('value') or ''
            types = result['types']['value'].replace('http://www.wikidata.org/entity/','')
            instances.append(cls(
                qid=qid,
                cidr=cidr,
                label=label,
                types_comma=types))

        # recreate everything
        cls.objects.bulk_create(instances, batch_size=batch_size)


    def __str__(self):
        return "%s -> %s" % (str(self.cidr),self.qid)

    @property
    def types(self):
        return self.types_comma.split(',')

    def json(self):
        nice_cidr = IPNetwork(str(self.cidr))
        if nice_cidr.is_ipv4_mapped():
            nice_cidr = nice_cidr.ipv4()

        return {
            'cidr':str(nice_cidr),
            'qid':self.qid,
            'name':self.label,
            'short_name': self.short_label,
            'types':self.types,
        }

    @property
    def short_label(self):
        if not ' ' in self.label:
            return self.label
        initials_re = re.compile(r'[A-Z0-9]')
        initials = ''.join(initials_re.findall(unidecode(self.label)))
        if len(initials) > 1:
            return initials
        return self.label

    @property
    def wikidata_url(self):
        return "https://www.wikidata.org/wiki/"+self.qid
