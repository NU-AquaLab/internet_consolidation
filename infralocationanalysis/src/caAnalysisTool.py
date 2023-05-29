from collections import Counter
import json
import tldextract
import matplotlib as mpl

mpl.use('agg')
from pathlib import Path
import matplotlib.pyplot as plt
import os
import dns.resolver
import re
import statistics
import numpy as np
from scipy.stats import pearsonr

jsonPath = f"{Path(__file__).parent.parent}/data/alexaTop500SitesCountries.json"


def mergeSameCAs(CA):
    if CA == "Baltimore":
        CA = "DigiCert Inc"
    elif CA == "GlobalSign nv-sa":
        CA = "GlobalSign"
    elif CA == "COMODO CA Limited":
        CA = "Comodo CA Limited"
    elif CA == "GoDaddy.com, Inc.":
        CA = "The Go Daddy Group, Inc."
    return CA


def collectResults(caResults):
    # caResults=json.load(open("results/caResults.json"))
    caCountByCountry = {}
    resultsdict = {}
    # transitiveCA_DNSDict=json.load(open("results/transitiveCA_DNSDict.json"))
    # transitiveCA_CDNDict=json.load(open("results/transitiveCA_CDNDict.json"))

    alexaRegionalSites = json.load(open(jsonPath))
    top100_US = alexaRegionalSites["US"][:100]
    websiteCount = 500

    top5CAWebsitesList = []
    uniqueHTTPsWebsites = []

    for country in caResults:
        # if country=="CN":
        # 	continue
        OCSPEnabled = 0
        HTTPS = 0
        third = 0
        private = 0
        thirdHTTPS = 0
        OCSPHTTPS = 0
        mostPopularCA = 0
        criticallyDependent = 0
        transitiveCA_DNSThird = 0
        transitiveCA_CDNThird = 0
        HTTPStop100 = 0
        thirdtop100 = 0
        OCSPEnabledtop100 = 0
        if country not in caCountByCountry:
            caCountByCountry[country] = {}
        for website in caResults[country]:
            # if website not in top100_US:
            # 	continue
            if caResults[country][website]["OCSP"] == "OCSP enabled":
                OCSPEnabled += 1
                if website in top100_US:
                    OCSPEnabledtop100 += 1
            if caResults[country][website]["HTTP/s"] == "HTTPS":
                if website not in uniqueHTTPsWebsites:
                    uniqueHTTPsWebsites.append(website)
                HTTPS += 1
                if website in top100_US:
                    HTTPStop100 += 1
                if caResults[country][website]["type"] == "third" or caResults[country][website]["CA_URL"] == "THIRD":
                    thirdHTTPS += 1
                    if caResults[country][website]["OCSP"] != "OCSP enabled":
                        criticallyDependent += 1
                if caResults[country][website]["OCSP"] == "OCSP enabled":
                    OCSPHTTPS += 1
            if caResults[country][website]["type"] == "third" or caResults[country][website]["CA_URL"] == "THIRD":
                third += 1
                if website in top100_US:
                    thirdtop100 += 1
            # else:
            # 	if country in transitiveCA_DNSDict:
            # 		if caResults[country][website]["CA"] in transitiveCA_DNSDict[country]:
            # 			transitiveCA_DNSThird+=1
            # 			# print ("CA_DNSWebiste: ",website)

            # 	if country in transitiveCA_CDNDict:
            # 		if caResults[country][website]["CA"] in transitiveCA_CDNDict[country]:
            # 			# print ("CA_CDNWebiste: ",website)
            # 			transitiveCA_CDNThird+=1

            if caResults[country][website]["type"] == "private" or caResults[country][website]["CA_URL"] == "FIRST":
                private += 1
            CA = caResults[country][website]["CA"]
            if CA != "":
                # uncomment this for ratio of popular over thirdparty
                if caResults[country][website]["type"] == "third" or caResults[country][website]["CA_URL"] == "THIRD":
                    CA = mergeSameCAs(CA)  # merge CAs that belong from the same provider
                    if CA not in caCountByCountry[country]:
                        caCountByCountry[country][CA] = 1
                    else:
                        caCountByCountry[country][CA] += 1
        # change value here to 5 for top 5
        fivePopularCAs = dict(Counter(caCountByCountry[country]).most_common(3))

        fivePopularCAsCount = 0
        for value in fivePopularCAs.values():
            fivePopularCAsCount += value
        print(country, fivePopularCAs, 100 * fivePopularCAsCount / websiteCount)
        top5CAWebsitesList.append(100 * fivePopularCAsCount / websiteCount)

        _max = 0
        mostpopularCA = ""
        for ca in caCountByCountry[country]:
            if caCountByCountry[country][ca] > _max and ca != "":
                _max = caCountByCountry[country][ca]
                mostpopularCA = ca
        MostPopularCAThird = 0
        for website in caResults[country]:
            if caResults[country][website]["type"] == "third" or caResults[country][website]["CA_URL"] == "THIRD":
                CA = caResults[country][website]["CA"]
                CA = mergeSameCAs(CA)
                if CA == mostpopularCA:
                    MostPopularCAThird += 1

        allCAs = dict(Counter(caCountByCountry[country]))

        popularCAs = []
        for ca in fivePopularCAs:
            popularCAs.append(ca)
        # print (country,fivePopularCAs,fivePopularCAsCount)

        if country not in resultsdict:
            resultsdict[country] = {}

        resultsdict[country]["OCSP"] = 100 * OCSPEnabled / websiteCount
        resultsdict[country]["HTTPS"] = 100 * HTTPS / websiteCount
        resultsdict[country]["third"] = 100 * third / websiteCount
        resultsdict[country]["transitiveCA_DNSThird"] = transitiveCA_DNSThird
        resultsdict[country]["transitiveCA_CDNThird"] = transitiveCA_CDNThird
        resultsdict[country]["private"] = 100 * private / websiteCount
        if HTTPS != 0:
            resultsdict[country]["thirdHTTPS"] = 100 * thirdHTTPS / HTTPS
            resultsdict[country]["OCSPHTTPS"] = 100 * OCSPHTTPS / HTTPS
        resultsdict[country]["criticallyDependent"] = 100 * criticallyDependent / websiteCount
        resultsdict[country]["mostpopularCA"] = mostpopularCA

        resultsdict[country]["OCSPtop100"] = 100 * OCSPEnabledtop100 / 100
        resultsdict[country]["HTTPStop100"] = 100 * HTTPStop100 / 100
        resultsdict[country]["thirdtop100"] = 100 * thirdtop100 / 100

        # uncomment this for ratio of popular over thirdparty
        thirdCount = websiteCount * resultsdict[country]["third"] / 100
        if thirdCount != 0:
            resultsdict[country]["MostPopularCAThird"] = 100 * MostPopularCAThird / thirdCount
            resultsdict[country]["fivePopularCAsCount"] = 100 * fivePopularCAsCount / thirdCount
        resultsdict[country]["fivePopularCAs"] = popularCAs
        resultsdict[country]["caCountByCountry"] = caCountByCountry

        resultsdict[country]["allCAs"] = allCAs
        resultsdict[country]["consolidation"] = find_consolidation(caResults, country)

    print("Top 3 CA count min: ", min(top5CAWebsitesList), " avg: ",
          (sum(top5CAWebsitesList) / len(top5CAWebsitesList)), " max: ", max(top5CAWebsitesList))
    print("Total unique websites using HTTPs: ", len(uniqueHTTPsWebsites))

    # with open("results/caCountByCountry.json", 'w') as fp:
    # 	json.dump(caCountByCountry, fp)
    # with open("results/caAnalysis.json", 'w') as fp:
    # 	json.dump(resultsdict, fp)
    # with open("results/caAnalysisUS500.json", 'w') as fp:
    # 	json.dump(resultsdict["US"], fp)

    # print ("\n\n",resultsdict)
    return resultsdict


def find_consolidation(caResults, country):
    top5List = ["DigiCert", "Comodo", "IdenTrust", "GlobalSign", "Starfield"]

    consolidation = 0
    for site in caResults[country]:
        for top5 in top5List:
            if top5.lower() in caResults[country][site]["CA"].lower():
                consolidation += 1
                break

    consolidation_score = 100 * consolidation / 500
    print(country, consolidation_score)
    return consolidation_score


def plotCAPlots():
    resultsdict = collectResults()
    # resultsdict=json.load(open("results/caCountByCountry.json"))

    countryList = []
    with open("data/countryList.txt", "r") as f:
        for country in f:
            countryList.append(str(country)[:-1])


if __name__ == "__main__":
    plotCAPlots()

# criticallyDependent=a site that 1) uses HTTPS, 2) uses a third-party CA, and 3) doesn’t use OCSP stapling.
# % Using Top 5 CAs in Country from HTTPS
