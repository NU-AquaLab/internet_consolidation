import dns.resolver
import tldextract
import subprocess
import os
import json
import re
from pathlib import Path
import sys
from datetime import datetime


def ThirdPartyDNS(website, dict):
    # Finds the SANList of the website
    SANList = []
    try:
        cmd = 'openssl s_client -connect ' + website + ':443 </dev/null 2>/dev/null | openssl x509 -noout -text | grep DNS'
        mycmd = subprocess.getoutput(cmd)
        list = str(mycmd).split(' DNS:')
        for item in list:
            SANList.append(item[:-1])
    except Exception as e:
        print("not support HTTPS")

    try:
        answers = dns.resolver.query(website, 'NS')
    except Exception as e:
        print("error in finding nameservers", website, str(e))
        return

    nameservers = []
    for server in answers:
        try:
            nameservers.append(str(server.target))
        except Exception as e:
            print("error in finding server target", website, server, str(e))
            continue

    for ns in nameservers:
        ns_type = "unknown"
        provider = ns
        try:
            if tldextract.extract(website).domain == tldextract.extract(ns).domain:
                ns_type = "private"
        except Exception as e:
            print("error in tld matching", website, ns, str(e))
        if ns_type != "private":
            for item in SANList:
                # print (website,tldextract.extract(ns).domain,SANList)
                try:
                    if str(tldextract.extract(ns).domain) in item:
                        print("identified by SANList: ", website, ns, item)
                        ns_type = "private"
                        break
                except Exception as e:
                    print("error in SANList matching", website, ns, str(e))

        if ns_type != "private":
            try:
                answer = dns.resolver.query(ns, 'SOA', raise_on_no_answer=False)
                if answer.rrset is None:
                    soa_ns = str(answer.response.authority[0]).split(" ")[0]

                soa_w_answers = dns.resolver.query(website, 'SOA')
                soa_w = soa_w_answers[0].mname

                soaw_simplified = re.sub(r'\d+', '', tldextract.extract(str(soa_w)).domain)
                soans_simplified = re.sub(r'\d+', '', tldextract.extract(str(soa_ns)).domain)

                if soaw_simplified != soans_simplified:
                    print("identified by SOA: ", website, ns)
                    ns_type = "third"
                    print(website, " type=", ns_type, " NS_SOA= ", str(soa_ns), " website_SOA= ", str(soa_w))

            except Exception as e:
                print("error in soa matching", website, ns, str(e))

        if website not in dict:
            dict[website] = {}
            dict[website]["ns_type"] = []
            dict[website]["provider"] = []
        if provider not in dict[website]["provider"]:
            dict[website]["provider"].append(provider)
            dict[website]["ns_type"].append(ns_type)


def start_dns(countryCode):
    print("country_code is:", countryCode)
    #  file that has Google Top1000 per Country
    jsonPath = f"{Path(__file__).parent.parent}/data/alexaTop500SitesCountries.json"
    with open(jsonPath, mode="r") as jsonFile:
        jsonData = json.load(jsonFile)
    websites = jsonData[countryCode]

    if not os.path.exists("../results"):
        os.mkdir("../results")

    dict = {}
    i = 0
    for website in websites:
        print(100 * i / len(websites), " \% complete", website)
        ThirdPartyDNS(website, dict)
        i += 1

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    aggregatedResults = {}
    aggregatedResults[countryCode] = dict

    return aggregatedResults


if __name__ == "__main__":
    start_dns(sys.argv[1])
