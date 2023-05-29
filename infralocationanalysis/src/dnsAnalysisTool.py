import json
import tldextract
import matplotlib as mpl

mpl.use('agg')
from pathlib import Path
import os
import re

project_path = os.path.dirname(os.path.abspath(__file__))


def findUnique(ns, array):
    domain = tldextract.extract(ns).domain
    notUnique = 0
    for uniqueNS in array:
        if domain == tldextract.extract(uniqueNS).domain:
            notUnique = 1
            break
    if notUnique == 0:
        for uniqueNS in array:
            soaw_simplified = re.sub(r'\d+', '', domain)
            soans_simplified = re.sub(r'\d+', '', tldextract.extract(uniqueNS).domain)

            if soaw_simplified == soans_simplified:
                notUnique = 1
                break

    if notUnique == 0:
        return True
    else:
        return False


def collectResults(dnsResults, rerun, country_code):
    websiteCount = 500
    jsonPath_alexa = f"{Path(__file__).parent.parent}/data/alexaTop500SitesCountries.json"
    jsonPath_analy = f"{Path(__file__).parent.parent}/results/dns_centralization_analysis_" + country_code + ".json"
    jsonPath_analy_updated = f"{Path(__file__).parent.parent}/results/dns_centralizationResultsUpdated.json"
    jsonPath_provider = f"{Path(__file__).parent.parent}/results/largeDNSProvider.json"

    alexaRegionalSites = json.load(open(jsonPath_alexa))
    top100_US = alexaRegionalSites["US"][:100]
    if rerun == 1:
        largeDNSProvider = {}
        initialResults = json.load(open(jsonPath_analy))
        for country in dnsResults:
            largeDNSProvider[country] = []
            for website in dnsResults[country]:
                ind = 0
                for ns_type in dnsResults[country][website]["ns_type"]:
                    if ns_type == "unknown":
                        ns = dnsResults[country][website]["provider"][ind]
                        dnsDomain = tldextract.extract(ns).domain
                        dnsDomain = re.sub(r'\d+', '', dnsDomain)
                        # print (country,website,ns)
                        if initialResults[country]["dnsproviders"][dnsDomain] >= 50:
                            dnsResults[country][website]["ns_type"][ind] = "third"
                            if dnsDomain not in largeDNSProvider[country]:
                                largeDNSProvider[country].append(dnsDomain)
        with open(jsonPath_analy_updated, 'w') as fp:
            json.dump(dnsResults, fp)

    resultsdict = {}
    top5DNSWebsitesList = []
    for country in dnsResults:
        # if country=="CN":
        # 	continue
        uniqueNSDict = {}
        uniqueNSThirdDict = {}
        thirdParty = 0
        dnsproviders = {}
        thirddnsproviders = {}
        CritDep = 0
        thirdNdPrivate = 0
        singleThird = 0
        redundant = 0
        TrueRedundant = 0
        multipleThirdParty = 0
        top100counter = 0

        thirdPartytop100 = 0
        redundanttop100 = 0
        multipleThirdPartytop100 = 0
        singleThirdtop100 = 0
        thirdNdPrivatetop100 = 0

        for website in dnsResults[country]:

            uniqueNSDict[website] = []
            uniqueNSThirdDict[website] = []
            # how many websites are redundantly provisioned with dns
            potentialRedundancy = False
            ind = 0
            uniqueNSList = []
            uniqueThirdPartyNS = []

            for ns_type in dnsResults[country][website]["ns_type"]:
                if ns_type == "private":
                    potentialRedundancy == True

                ns = dnsResults[country][website]["provider"][ind]
                ind += 1
                if len(uniqueNSList) == 0:
                    uniqueNSList.append(ns)
                else:
                    unique = findUnique(ns, uniqueNSList)
                    if unique:
                        uniqueNSList.append(ns)
            # print (website, " unique overall: ",uniqueNSList)

            if len(uniqueNSList) > 1:
                redundant += 1
                if website in top100_US:
                    redundanttop100 += 1
                if potentialRedundancy:
                    TrueRedundant += 1

            if "third" in dnsResults[country][website]["ns_type"]:
                # print (website,dnsResults[country][website]["ns_type"])
                index = 0
                # if top100counter<100:
                if website in top100_US:
                    thirdPartytop100 += 1
                # how many websites use thirdparty dns
                thirdParty += 1

                # websites using both third party and private
                if "private" in dnsResults[country][website]["ns_type"]:
                    thirdNdPrivate += 1
                    if website in top100_US:
                        thirdNdPrivatetop100 += 1

                for ns_type in dnsResults[country][website]["ns_type"]:
                    ns = dnsResults[country][website]["provider"][index]
                    index += 1
                    if ns_type != "third":
                        continue

                    # finding unique thridy party dns providers used by a website
                    if len(uniqueThirdPartyNS) == 0:
                        uniqueThirdPartyNS.append(ns)
                    else:
                        unique = findUnique(ns, uniqueThirdPartyNS)
                        if unique:
                            uniqueThirdPartyNS.append(ns)

                if len(uniqueThirdPartyNS) > 1:
                    multipleThirdParty += 1
                    if website in top100_US:
                        multipleThirdPartytop100 += 1

                # websites critically dependant on a single 3rd party provider
                if len(uniqueThirdPartyNS) == 1:

                    if len(uniqueNSList) == 1:
                        singleThird += 1
                        if website in top100_US:
                            singleThirdtop100 += 1
            # print (website," unique 3rd: ",uniqueThirdPartyNS)

            # freq of all providers used by all domains
            for _dns in uniqueNSList:
                dnsDomain = tldextract.extract(_dns).domain
                dnsDomain = re.sub(r'\d+', '', dnsDomain)
                if dnsDomain not in dnsproviders:
                    dnsproviders[dnsDomain] = 0
                dnsproviders[dnsDomain] += 1
                if dnsDomain not in uniqueNSDict[website]:
                    uniqueNSDict[website].append(dnsDomain)

            # uncomment this for ratio of popular over thirdparty
            if len(uniqueThirdPartyNS) != 0:
                for _dns in uniqueThirdPartyNS:
                    dnsDomain = tldextract.extract(_dns).domain
                    dnsDomain = re.sub(r'\d+', '', dnsDomain)
                    if dnsDomain not in thirddnsproviders:
                        thirddnsproviders[dnsDomain] = 0
                    thirddnsproviders[dnsDomain] += 1
                    if dnsDomain not in uniqueNSThirdDict[website]:
                        uniqueNSThirdDict[website].append(dnsDomain)

            top100counter += 1

        if rerun == 0:
            sorteddnsproviders = dict(sorted(dnsproviders.items(), key=lambda item: item[1]))
        else:
            sorteddnsproviders = dict(sorted(dnsproviders.items(), key=lambda item: item[1]))

        if country not in resultsdict:
            resultsdict[country] = {}
        resultsdict[country]["3rdPartyReliance"] = 100 * thirdParty / 500
        resultsdict[country]["criticallyDependant"] = 100 * singleThird / 500
        resultsdict[country]["3rdndPrivate"] = 100 * thirdNdPrivate / 500
        resultsdict[country]["redundant"] = 100 * redundant / 500
        resultsdict[country][
            "TrueRedundant"] = 100 * TrueRedundant / 500  # check rname and mname logic for this from paper
        resultsdict[country][
            "multipleThirdParty"] = 100 * multipleThirdParty / 500  # check rname and mname logic for this from paper
        resultsdict[country]["dnsproviders"] = sorteddnsproviders
        resultsdict[country]["thirddnsproviders"] = thirddnsproviders

        resultsdict[country]["3rdPartyReliancetop100"] = 100 * thirdPartytop100 / 100
        resultsdict[country]["criticallyDependenttop100"] = 100 * singleThirdtop100 / 100
        resultsdict[country]["3rdndPrivatetop100"] = 100 * thirdNdPrivatetop100 / 100
        resultsdict[country]["redundanttop100"] = 100 * redundanttop100 / 100
        resultsdict[country]["multipleThirdPartytop100"] = 100 * multipleThirdPartytop100 / 100
        resultsdict[country]["consolidation"] = find_consolidation(dnsResults, country)

    if not os.path.exists(project_path + "/results"):
        os.mkdir(project_path + "/results")
    if rerun == 0:
        with open(jsonPath_analy, 'w') as fp:
            json.dump(resultsdict, fp)
    if rerun != 0:
        with open(jsonPath_analy_updated, 'w') as fp:
            json.dump(resultsdict, fp)

        with open(jsonPath_provider, 'w') as fp:
            json.dump(largeDNSProvider, fp)

    return resultsdict


def find_consolidation(dnsResults, country):
    top5List = ["cloudflare", "awsdns", "nsone", "akam", "ultradns"]

    consolidation = 0
    for site in dnsResults[country]:
        consolidationBool = False
        for provider in dnsResults[country][site]["provider"]:
            for top5 in top5List:
                if top5 in provider:
                    consolidation += 1
                    consolidationBool = True
                    break
            if consolidationBool:
                break

    consolidation_score = 100 * consolidation / 500
    print(country, consolidation_score)

    return consolidation_score


def plotDNSPlots(dnsResults, country_code):
    resultsdict = collectResults(dnsResults, 0, country_code)  # collects all metrics
    resultsdict = collectResults(dnsResults, 1, country_code)  # collects all metrics

    jsonPath = f"{Path(__file__).parent.parent}/results/dns_centralizationResultsUpdated.json"
    resultsdict = json.load(open(jsonPath))
    return resultsdict


if __name__ == "__main__":
    plotDNSPlots()
