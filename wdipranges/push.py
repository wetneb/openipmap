from netaddr import IPAddress
from netaddr import IPNetwork
from netaddr import iprange_to_cidrs
from netaddr import cidr_merge
from collections import defaultdict
import sys
import io
import pywikibot
from datetime import date
from pywikibot import pagegenerators as pg

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
site.login()

ipv4_pid = 'P3761'
ipv6_pid = 'P3793'
url_ref_pid = 'P854'
retrieved_pid = 'P813'
start_date_pid = 'P580'
summary = 'merged IP ranges'

def check_safe_type(qid):
    query = ("""
    SELECT ?item WHERE {
       wd:%s wdt:P31 ?item .
       { ?item wdt:P279* wd:Q1048835 } UNION
       { ?item wdt:P279* wd:Q847017 }
    }""" % qid)
    for page in pg.WikidataSPARQLPageGenerator(query, site=site):
        return False
    return True


def wbtime_of_date(python_date):
    wbtime = pywikibot.WbTime(year=python_date.year,
        month=python_date.month, day=python_date.day, precision='day')
    return wbtime

def add_ranges(qid, ranges, created_dates={}):
    """
    Ranges is supposed to be a dict "range" -> "reference URL"
    Created_dates is a dict "range" -> date of creation
    """
    item = pywikibot.ItemPage(repo, qid)
    # first, compute the new list of merged ranges
    range_to_claim = {}
    all_claims = item.get()['claims']
    for claim in all_claims.get(ipv4_pid, [])+all_claims.get(ipv6_pid, []):
        rng = IPNetwork(claim.getTarget())
        range_to_claim[rng] = claim

    new_ranges = list(range_to_claim) + list(ranges)
    merged_new_ranges = cidr_merge(new_ranges)

    claims_to_remove = []
    print('merged ranges')
    print(merged_new_ranges)

    # if the type is dangerous, skip
    if not check_safe_type(item.title()):
        print("Ignoring item: dangerous type")
        return

    # find each missing range
    for rng in merged_new_ranges:
        if rng not in range_to_claim:
            print('new range')
            print(rng)

            # create a new claim
            pid = ipv4_pid if rng.version == 4 else ipv6_pid
            new_claim = pywikibot.Claim(repo, pid)
            new_claim.setTarget(str(rng))
            item.addClaim(new_claim)

            # add created date if provided
            created_date = created_dates.get(rng)
            if created_date:
                start_claim = pywikibot.Claim(repo, start_date_pid)
                start_claim.setTarget(wbtime_of_date(created_date))
                new_claim.addQualifier(start_claim)

            # gather all the sources from the previously overlapping
            # claims
            print('gathering sources from existing claims')
            for old_range, old_claim in range_to_claim.items():
                if rng in old_range.supernet():
                    for old_source in old_claim.getSources():
                        new_claim.addSources(list(old_source.values())[0])
                    print('removing old claim')
                    print(old_claim)
                    claims_to_remove.append(old_claim)

            # gather all the sources from the new ranges
            print('gathering sources from new claims')
            for added_range, source_url in ranges.items():
                if rng in added_range.supernet() or rng == added_range:
                    source_claim = pywikibot.Claim(repo, url_ref_pid)
                    source_claim.setTarget(source_url)
                    date_claim = pywikibot.Claim(repo, retrieved_pid)
                    retrieved_date = wbtime_of_date(date.today())
                    date_claim.setTarget(retrieved_date)
                    new_claim.addSources([source_claim, date_claim])

    # remove old claims
    if claims_to_remove:
        site.removeClaims(claims_to_remove, summary=summary)


