import json
import os
import re
import subprocess
import sys
import time
import Pen
import psutil
import pathlib
from datetime import datetime
from os.path import join

import dns.resolver
import findcdn
import selenium.webdriver.remote.utils as utils
import tldextract
from browsermobproxy import Server
from selenium import webdriver
from github_config import git_upload_file
from webdriver_manager.chrome import ChromeDriverManager
from browsermobproxy.exceptions import ProxyServerError
from selenium.common.exceptions import TimeoutException, WebDriverException

project_path = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(project_path, '..', 'data')
TOP_SITES_FILE = os.path.join(DATA_PATH, 'alexaTop500SitesCountries.json')


def create_dir_if_not_exists(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def get_SAN(website, country):
    if not os.path.exists("results/SANs"):
        os.mkdir("results/SANs")
    try:
        sanDict = json.load(open("results/SANs/SanList_" + country + ".json"))
    except:
        sanDict = {}
    if website in sanDict:
        # if "unable to load certificate" not in sanDict[website][0]:
        return sanDict[website]
    SANList = []
    try:
        cmd = 'openssl s_client -connect ' + website + ':443 </dev/null 2>/dev/null | openssl x509 -noout -text | grep DNS'
        mycmd = subprocess.getoutput(cmd)
        list = str(mycmd).split(' DNS:')
        for item in list:
            SANList.append(item[:-1])
    except Exception as e:
        Pen.write(f"does not support HTTPS", color='WARNING')
    sanDict[website] = SANList
    dump_json(sanDict, 'results/SANs/SanList_' + country + '.json')
    return SANList


# --code for internal resources----------------
class HARGenerator():
    # This class is used to interact with BrowserMob Proxy, see here: https://github.com/lightbody/browsermob-proxy
    # Source code for Python API is: https://browsermob-proxy-py.readthedocs.io/en/latest/_modules/browsermobproxy/server.html#Server
    # Please make sure your system has the required Java runtime for the server to run properly.

    def __init__(self):
        self.port = 8090
        self.bmp_log_path = os.path.join(project_path, '..', 'logs', 'bmp')
        create_dir_if_not_exists(self.bmp_log_path)
        self.chrome_driver_log_path = os.path.join(project_path, '..', 'logs', 'chromedriver')
        create_dir_if_not_exists(self.chrome_driver_log_path)

        self.terminated = False

        try:
            Pen.write(f"Initiating server...", color='OKGREEN', newline=False)
            self.server = Server(
                path=os.path.join(project_path, '..', 'browsermob-proxy-2.1.4', 'bin', 'browsermob-proxy'),
                options={'port': self.port})
            Pen.write(f"OK", color='OKGREEN')

            Pen.write(f"Starting server...", color='OKGREEN', newline=False)
            self.server.start(options={
                'log_file': f'{datetime.now().strftime("%Y-%m-%d-%H:%M:%S")}.log',
                'log_path': self.bmp_log_path,
                'retry_count': 5
            })
            Pen.write(f"OK", color='OKGREEN')

        except ProxyServerError as err:
            Pen.write(f"Error starting server. Please check server logs. Exiting...", color='FAIL')
            Pen.write(str(err), color='FAIL')
            exit(-1)

        Pen.write(f"Creating proxy server...", color='OKGREEN', newline=False)
        self.proxy = self.server.create_proxy(params={"trustAllServers": "true"})
        Pen.write(f"OK", color='OKGREEN')

        Pen.write(f"Creating Chrome driver...", color='OKGREEN', newline=False)
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=self._chrome_options())
        Pen.write(f"OK", color='OKGREEN')

    def _chrome_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--proxy-server={}".format(self.proxy.proxy))
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--headless")
        options.add_argument("--no-cache")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--verbose")
        options.add_argument(f"--log-path={self.chrome_driver_log_path}")

        return options

    def __del__(self):
        if not self.terminated:
            Pen.write(
                f"Clean up on HARGenerator object deletion. Did you forget to explicitly terminate HARGenerator object?",
                color='WARNING')
            self.terminate()

    def terminate(self):
        try:
            # BrowserMobProxy starts a process (parent process), which starts another process running the proxy server (child process)
            # Calling self.server.stop() only stops the parent process but not the child process, which becomes a zombie process when the program ends
            Pen.write(f"Cleaning up HAR object...", color='OKGREEN')

            for child in psutil.Process(self.server.process.pid).children(recursive=True):
                Pen.write(f"Killing child process {child.pid}...", color='OKGREEN', newline=False)
                child.kill()
                Pen.write(f"OK", color='OKGREEN')
            Pen.write(f"Killing BMP server...", color='OKGREEN', newline=False)
            self.server.stop()
            Pen.write(f"OK", color='OKGREEN')

            Pen.write(f"Killing Chrome driver...", color='OKGREEN', newline=False)
            self.driver.quit()
            time.sleep(
                1)  # This is to prevent "ImportError: sys.meta_path is None, Python is likely shutting down" from Selenium, see here: https://stackoverflow.com/questions/41480148/importerror-sys-meta-path-is-none-python-is-likely-shutting-down
            Pen.write(f"OK", color='OKGREEN')

            self.terminated = True
        except ImportError:
            pass  # Ignore "ImportError: sys.meta_path is None, Python is likely shutting down"

    def get_har(self, hostname):
        self.proxy.new_har(hostname)
        try:
            self.driver.set_page_load_timeout(60)
            self.driver.get(f'https://{hostname}')
        except TimeoutException as err:
            Pen.write(f'Timeout from renderer for {hostname}. Skipping...', 'FAIL')
        except WebDriverException as err:
            Pen.write(f'ERR_TUNNEL_CONNECTION_FAILED from renderer for {hostname}. Skipping...', 'FAIL')
        except Exception as err:
            Pen.write(f'Unexpected error: {err}.\n Skipping...', 'FAIL')

        time.sleep(1)

        return self.proxy.har

    def get_hars(self, hostnames):
        hars = list()
        for i, hostname in enumerate(hostnames):
            hars.append(self.get_har(hostname))

        return hars


class Resource_collector:
    def __init__(self):
        self.resources = []

    def dump(self, fn_prefix, country):
        utils.dump_json(self.resources, join(fn_prefix, "alexaResources" + country + ".json"))
        # utils.dump_json(self.resources, join(project_path,fn_prefix,"alexaResources"+country+".json"))

    # extracts all the resources from each har object
    # takes a list of har json objects
    # stores in the object resources
    def collect_resources(self, har):
        if har and "log" in har.keys() and "entries" in har["log"].keys():
            for entry in har["log"]["entries"]:
                resource = entry["request"]["url"]
                if resource not in self.resources:
                    self.resources.append(str(resource))
        return self.resources


def get_resources(website, hm):
    # use hars to find resources!
    rc = Resource_collector()
    hars = hm.get_har(website)
    return rc.collect_resources(hars)


# -----done with internal resources code ---------------------

def url_to_domain(url):
    ext = tldextract.extract(url)
    if ext[0] == '':
        ext = ext[1:]
    return ".".join(ext)


def get_tld(website):
    tld = tldextract.extract(website)
    return tld.domain


def CDN_private_third(cdn, website, website_cdn_Map, country):
    resolver = dns.resolver.Resolver()
    cnames = website_cdn_Map[cdn]
    SANList = get_SAN(website, country)
    third_party = None

    for cname in cnames:
        cn_tld = get_tld(cname)
        if cn_tld == "":
            cn_tld = cname
        if cn_tld == get_tld(website):
            return False
        for san in SANList:
            if cn_tld in san and san != " ":
                # Pen.write(f"identified by SANList: website: {website} cname: {cname}  san: {san}", color='OKGREEN')
                return False

        try:
            soa_w_answers = dns.resolver.resolve(website, 'SOA')
            soa_w = soa_w_answers[0].mname
            if cname[0] == ".":
                cname = cname[1:]

            answer = dns.resolver.resolve(cname, 'SOA', raise_on_no_answer=False)
            if answer.rrset is None:
                soa_cname = str(answer.response.authority[0]).split(" ")[0]
            else:
                soa_cname_answers = dns.resolver.resolve(cname, 'SOA')
                soa_cname = soa_cname_answers[0].mname

            soaw_simplified = re.sub(r'\d+', '', tldextract.extract(str(soa_w)).domain)
            soans_simplified = re.sub(r'\d+', '', tldextract.extract(str(soa_cname)).domain)
            if soaw_simplified != soans_simplified:
                # print ("identified by SOA: ",website, "CNAME_SOA: ",soa_cname, "website_SOA: ",soa_w,"\n")
                return True
        except Exception as e:
            Pen.write(f"error in soa matching {website}, {cname}, error is: {e}", color='WARNING')
            continue

    return third_party


def read_websites_country(country, filename):
    f = open(filename, 'r')
    data = json.load(f)
    websites = data[country]
    f.close()
    return websites


def dump_json(data, fn):
    with open(fn, 'w') as fp:
        json.dump(data, fp)


def collectResources(country, resourcesDict):
    filename = DATA_PATH + '/alexaTop500SitesCountries.json'
    hm = HARGenerator()

    website_iter = 0

    try:
        websites = read_websites_country(country, filename)

        for website in websites:
            website_iter += 1
            if website in resourcesDict:
                continue
            Pen.write(
                f"Collecting resources for hostname: {website} Progress: {website_iter + 1}/{len(websites)} "
                f"({(website_iter + 1) * 100 / len(websites):.2f}%)", color='OKCYAN')
            # Pen.write("country: " + country + " ,website: " + website + " ,num: " + str(website_iter), color='OKGREEN')
            resourcesDict[website] = []
            resources = get_resources(website, hm)
            if resources == None:
                hm = HARGenerator()
                resources = get_resources(website, hm)
            resourcesDict[website] = resources
            dump_json(resourcesDict, 'results/resources/resources_' + country + '.json')
    finally:
        hm.terminate()


def runCDNMeasurements(country):
    resourcesPerCountry = json.load(open("results/resources/resources_" + country + ".json"))

    if not os.path.exists("results/internal_resources"):
        os.mkdir("results/internal_resources")

    try:
        internalResourcesMap = json.load(open('results/internal_resources/internal_resources_' + country + '.json'))
    except:
        Pen.write(f"internal resources Map doesn't exist for the country: {country}", color="WARNING")
        internalResourcesMap = findInternalResources(resourcesPerCountry, country)
        cdn_file_name = "internal_resources_" + country + ".json"
        cdn_src_file_path = "results/internal_resources/" + cdn_file_name
        git_upload_file("cdn/" + cdn_file_name, cdn_src_file_path)

    all_domains = []
    website_domains_map = {}
    count = 0
    for website in internalResourcesMap:
        count += 1

        internal_resources = []
        if website not in website_domains_map:
            website_domains_map[website] = []

        for resource in internalResourcesMap[website]:
            if resource not in internal_resources:
                internal_resources.append(resource)

        for resource in internal_resources:
            domain = url_to_domain(resource)
            if 'www.' in domain:
                domain = domain.replace('www.', '')
            if domain not in all_domains:
                all_domains.append(domain)
            if domain not in website_domains_map[website]:
                website_domains_map[website].append(domain)
    Pen.write(f"len of all domains: {len(all_domains)}", color="OKGREEN")

    # run cdn measurements on internal resources only
    return analyseResources(internalResourcesMap, website_domains_map, country, "internal")


def extract_error_domains(e):
    error_message = str(e)
    # assuming the error message is of the form "<domain_name> is not a valid domain in findcdn.main()"
    return error_message.split()[0].strip()


def find_cdn_recursive(all_domains, country, output_path, double_in=True, threads=23):
    print("find_cdn_recursive with country: ", country)
    try:
        resp_json = findcdn.main(all_domains, output_path=output_path, double_in=double_in, threads=threads)
        dumped_domaintoCDN = json.loads(resp_json)
        return dumped_domaintoCDN
    except findcdn.findcdn_err.InvalidDomain as e:
        print("Error: Invalid domain name")
        print(e)
        error_domain = extract_error_domains(e)  # extract error domains from the exception object
        print("extract_error_domains is: ", error_domain)
        all_domains.remove(error_domain)  # remove the error domains from the list
        return find_cdn_recursive(all_domains, country, output_path, double_in, threads)
    except Exception as e:
        print("Error: An unexpected error occurred")
        print(e)
        return {}


def analyseResources(resourcesPerCountry, website_domains_map, country, resourceType):
    total_cdns = {}

    if not os.path.exists("results/my_domainCDNMap"):
        os.mkdir("results/my_domainCDNMap")
    if not os.path.exists("results/my_CNames_of_domains_map"):
        os.mkdir("results/my_CNames_of_domains_map")

    all_domains = []
    for website in website_domains_map:
        for domain in website_domains_map[website]:
            if domain not in all_domains:
                all_domains.append(domain)
    Pen.write(f"internal resources: {len(all_domains)}", color='OKGREEN')

    if not os.path.exists("results/total_cdns_internal"):
        os.mkdir("results/total_cdns_internal")

    try:
        dumped_domaintoCDN = json.load(open("results/my_domainCDNMap/outputCDN_" + country + ".json"))
    except:
        dumped_domaintoCDN = find_cdn_recursive(all_domains, country,
                                                "results/my_domainCDNMap/outputCDN_" + country + ".json")
        if len(dumped_domaintoCDN) == 0:
            print("find_cdn_recursive returns empty dict: ", dumped_domaintoCDN)
            return dumped_domaintoCDN

    cdn_file_name = "outputCDN_" + country + ".json"
    cdn_src_file_path = "results/my_domainCDNMap/" + cdn_file_name
    git_upload_file("cdn/" + cdn_file_name, cdn_src_file_path)

    count = 0
    for website in resourcesPerCountry:
        # Pen.write(f"Running for website: {website}, {100 * count / len(resourcesPerCountry)}", color='OKGREEN')
        count += 1
        website_cdn_Map = {}
        cdns = []
        for domain in website_domains_map[website]:
            if domain in dumped_domaintoCDN["domains"]:
                _cdns = dumped_domaintoCDN["domains"][domain]["cdns_by_names"]
                totalCDNs = []
                _cdns = _cdns.split(",")
                for cdn in _cdns:
                    _cdn = cdn.strip()
                    totalCDNs.append(_cdn.replace("'", ""))

                cnames = dumped_domaintoCDN["domains"][domain]["cdns"]
                totalCNames = []
                cnames = cnames.split(",")
                for cname in cnames:
                    _cname = cname.strip()
                    totalCNames.append(_cname.replace("'", ""))

                index = 0
                for cdn in totalCDNs:
                    if cdn not in cdns:
                        cdns.append(cdn)
                    if cdn not in website_cdn_Map:
                        website_cdn_Map[cdn] = []
                    website_cdn_Map[cdn].append(totalCNames[index])
                    index += 1
            for cdn in website_cdn_Map:
                website_cdn_Map[cdn] = list(set(website_cdn_Map[cdn]))
        # Pen.write(f"{website} map: {website_cdn_Map}", color='OKGREEN')

        if website not in total_cdns:
            total_cdns[website] = {}
        for cdn in cdns:
            private_third = CDN_private_third(cdn, website, website_cdn_Map, country)
            if private_third == True:
                total_cdns[website][cdn] = "ThirdParty"
            elif private_third == False:
                total_cdns[website][cdn] = 'Private'
            else:
                total_cdns[website][cdn] = 'Unknown'
            # Pen.write(f"{website}, {cdn}, {total_cdns[website][cdn]} \n", color='OKGREEN')

    dump_json(total_cdns, 'results/total_cdns_internal/total_cdns_' + country + '.json')
    return total_cdns


def findInternalResources(resourcesMap, country):
    internalResourcesMap = {}
    domainOwnersDict = json.load(open(DATA_PATH + '/domain_owners.json'))
    check = 0
    for website in resourcesMap:
        Pen.write(f"{website}, {100 * check / len(resourcesMap)}", color='OKGREEN')

        if website not in internalResourcesMap:
            internalResourcesMap[website] = []

        w_tld = get_tld(website)

        SANList = get_SAN(website, country)
        try:
            soa_w_answers = dns.resolver.resolve(website, 'SOA')
            soa_w = soa_w_answers[0].mname
        except Exception as e:
            Pen.write(f"{website}, {str(e)}", color='WARNING')
            soa_w = None

        domainOwnerentry = None
        for entry in domainOwnersDict:
            if website in entry["owner_name"]:
                domainOwnerentry = entry

        for resource in resourcesMap[website]:
            if website in resource or w_tld in resource:
                internalResourcesMap[website].append(resource)
                continue
            found = 0
            r_tld = get_tld(resource)
            if w_tld == r_tld:
                internalResourcesMap[website].append(resource)
                continue
            for san in SANList:
                if r_tld in san:
                    internalResourcesMap[website].append(resource)
                    found = 1
                    break
            if found == 1:
                continue

            if soa_w != None:
                try:
                    domain = url_to_domain(resource)
                    if 'www.' in domain:
                        domain = domain.replace('www.', '')
                    answer = dns.resolver.resolve(domain, 'SOA')
                    soa_cname = answer[0].mname
                except Exception as e:
                    try:
                        answer = dns.resolver.resolve(domain, 'SOA', raise_on_no_answer=False)
                        if answer.rrset is None:
                            soa_cname = str(answer.response.authority[0]).split(" ")[0]
                    except Exception as e:
                        Pen.write(f"{website}, {resource}, {r_tld}, {domain}, {str(e)}", color='WARNING')
                        soa_cname = None
                if soa_cname != None:
                    if soa_w != soa_cname:
                        soaw_simplified = re.sub(r'\d+', '', tldextract.extract(str(soa_w)).domain)
                        soacname_simplified = re.sub(r'\d+', '', tldextract.extract(str(soa_cname)).domain)
                        if soaw_simplified == soacname_simplified:
                            internalResourcesMap[website].append(resource)
                            continue
                    elif soa_w in soa_cname or soa_cname in soa_w:
                        internalResourcesMap[website].append(resource)
                        continue
            try:
                for domain in domainOwnerentry["domains"]:
                    if resource in domain or domain in resource:
                        internalResourcesMap[website].append(resource)
                        found = 1
                        break
                if found == 1:
                    continue
            except Exception as e:
                a = 1

    dump_json(internalResourcesMap, 'results/internal_resources/internal_resources_' + country + '.json')
    return internalResourcesMap


def runProgram(country):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    Pen.write(f"Current Start Time = {current_time}", color='OKGREEN')

    if not os.path.exists("results"):
        os.mkdir("results")

    if not os.path.exists("results/resources"):
        os.mkdir("results/resources")

    resourcesPerCountry = {}

    try:
        resourcesPerCountry = json.load(open("results/resources/resources_" + country + ".json"))
        Pen.write(f"Get cached data", color='OKGREEN')
    except:
        collectResources(country, resourcesPerCountry)
        cdn_file_name = "resources_" + country + ".json"
        cdn_src_file_path = "results/resources/" + cdn_file_name
        git_upload_file("cdn/" + cdn_file_name, cdn_src_file_path)

    cdn_list = runCDNMeasurements(country)
    total_cdn = {country: cdn_list}
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    Pen.write(f"Current End Time = {current_time}", color='OKGREEN')
    return total_cdn


if __name__ == "__main__":
    runProgram(sys.argv)
