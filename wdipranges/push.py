from netaddr import IPAddress
from netaddr import IPNetwork
from netaddr import iprange_to_cidrs
from netaddr import cidr_merge
from collections import defaultdict
import sys
import io
import pywikibot
from pywikibot import pagegenerators as pg

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
site.login()

ipv4_pid = 'P3761'
ipv6_pid = 'P3793'
url_ref_pid = 'P854'
summary = 'merged IP ranges'

def add_ranges(qid, ranges):
    """
    Ranges is supposed to be a dict "range" -> "reference URL"
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

    # if there are a lot of new ranges, this is suspicious
    if len(merged_new_ranges) > 5:
        print("SKIPPING, too many ranges")
        return
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
                    new_claim.addSource(source_claim)

    # remove old claims
    if claims_to_remove:
        site.removeClaims(claims_to_remove, summary=summary)


