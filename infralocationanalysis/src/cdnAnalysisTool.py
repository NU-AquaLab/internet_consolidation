import json
import csv
import os.path
from os import path
import matplotlib.pyplot as plt
import statistics
import numpy as np
from collections import Counter
from scipy.stats import pearsonr
from scipy.stats import spearmanr
import scipy.stats
from github_config import git_upload_file


def parseCDNList():
    CDNs = []
    with open("data/allCDNList.txt", 'r') as f:
        for line in f:
            if line != "\n":
                CDNs.append(line[:-1])
    print(CDNs)
    return CDNs


def read_json(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
        return data


countries = []


def get_countries_from_csv(filename):
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                countries.append(row[1])
            line_count += 1
    return countries


def total_cdns_analysis(country, resourceType):
    resultDict = {}
    resultDict[country] = {}
    _dict = {}
    # transitiveCDN_DNSDict=json.load(open("results/transitiveCDN_DNSDict.json"))
    websiteCount = 500
    alexaRegionalSites = json.load(open("../data/alexaTop500SitesCountries.json"))
    top100_US = alexaRegionalSites["US"][:100]

    if resourceType == "all":
        try:
            _dict = json.load(open('results/total_cdns/total_cdns_' + country + '.json'))
        except:
            return resultDict
    elif resourceType == "internal":
        try:
            _dict = json.load(open('results/total_cdns_internal/total_cdns_' + country + '.json'))
        except:
            return resultDict

    # total=0
    # for each country, for each cdn find if private of third
    third = 0
    transitiveThird = 0
    uniqueCDNs = []
    cdnWebsites = []
    thirdtop100 = 0
    for website in _dict.keys():
        # if website not in top100_US:
        # 	continue
        foundThird = 0
        if len(_dict[website].keys()) != 0:
            cdnWebsites.append(website)
        for cdn in _dict[website].keys():
            if _dict[website][cdn] == 'ThirdParty':
                if cdn not in uniqueCDNs:
                    uniqueCDNs.append(cdn)
                if website in top100_US:
                    thirdtop100 += 1
                third += 1
                foundThird = 1
                break
    # if foundThird==0:
    # 	if country in transitiveCDN_DNSDict:
    # 		for cdn in _dict[website].keys():
    # 			if cdn in transitiveCDN_DNSDict[country]:
    # 				transitiveThird+=1
    # 				break
    # total+=1
    resultDict[country]["ThirdParty"] = 100 * third / websiteCount
    resultDict[country]["transitiveThird"] = transitiveThird
    resultDict[country]["allCDNs"] = uniqueCDNs
    resultDict[country]["cdnWebsites"] = cdnWebsites

    critical_dependency = 0
    redundant = 0
    multipleThirdParty = 0

    critical_dependencytop100 = 0
    redundanttop100 = 0
    multipleThirdPartytop100 = 0
    for website in _dict.keys():
        # if website not in top100_US:
        # 	continue
        # cdns=[]
        # for cdn in _dict[website]:
        # 	found=0
        # 	for _cdn in cdns:
        # 		if _cdn.lower() in cdn.lower() or cdn.lower() in _cdn.lower():
        # 			found=1
        # 			break
        # 	if found==0:
        # 		cdns.append(cdn)
        if len(_dict[website]) == 1:

            # if len(cdns)==1:
            for value in _dict[website].values():
                if value == "ThirdParty":
                    if website in top100_US:
                        critical_dependencytop100 += 1
                    critical_dependency += 1
        elif len(_dict[website]) > 1:
            if website in top100_US:
                redundanttop100 += 1
            redundant += 1
            thirdcount = 0
            for value in _dict[website].values():
                if value == "ThirdParty":
                    thirdcount += 1
            if thirdcount > 1:
                if website in top100_US:
                    multipleThirdPartytop100 += 1
                multipleThirdParty += 1

    resultDict[country]["critical_dependency"] = 100 * critical_dependency / websiteCount
    resultDict[country]["redundant"] = 100 * redundant / websiteCount
    resultDict[country]["multipleThirdParty"] = 100 * multipleThirdParty / websiteCount

    resultDict[country]["critical_dependency_top100"] = 100 * critical_dependencytop100 / 100
    resultDict[country]["redundant_top100"] = 100 * redundanttop100 / 100
    resultDict[country]["multipleThirdParty_top100"] = 100 * multipleThirdPartytop100 / 100
    resultDict[country]["ThirdParty_top100"] = 100 * thirdtop100 / 100
    resultDict[country]["consolidation"] = find_consolidation()

    thirdndPrivate = 0
    for website in _dict.keys():
        thirdCDN = False
        privCDN = False
        for value in _dict[website].values():
            if value == "ThirdParty":
                thirdCDN = True
            if value == "Private":
                privCDN = True
        if thirdCDN and privCDN:
            thirdndPrivate += 1
    resultDict[country]["thirdndPrivate"] = 100 * thirdndPrivate / websiteCount

    return resultDict


def find_consolidation(cdnResults, country):
    top5List = ["Google", "Akamai", "Fastly", "Cloudflare", "Cloudfront"]

    consolidation = 0
    for site in cdnResults[country]:
        for top5 in top5List:
            if top5 in cdnResults[country][site]:
                consolidation += 1
                break

    consolidation_score = 100 * consolidation / 500
    print(country, consolidation_score)
    return consolidation_score


def run_analysis(country):
    cdnResults = {}
    _dict = json.load(open('results/total_cdns_internal/total_cdns_' + country + '.json'))
    cdnResults[country] = _dict
    cdn_file_name = "cdn_result_" + country + ".json"
    cdn_src_file_path = "results/" + cdn_file_name
    with open(cdn_src_file_path, 'w') as fp:
        json.dump(cdnResults, fp)
    git_upload_file("cdn/" + cdn_file_name, cdn_src_file_path)

    result_dict = total_cdns_analysis(country, "internal")
    return result_dict


if __name__ == "__main__":
    run_analysis()
