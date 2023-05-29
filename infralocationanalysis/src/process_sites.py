from pathlib import Path
import json
import pycountry

def process_sites_file():
    iso_data = {}
    json_path = f"{Path(__file__).parent.parent}/data/countryList.txt"
    json_res = f"{Path(__file__).parent.parent}/data/iso_map.json"
    iso_path = f"{Path(__file__).parent.parent}/data/iso.json"

    with open(json_path, mode="r") as f:
        lines = f.readlines()

    with open(iso_path, mode="r") as jsonFile:
        iso_data = json.load(jsonFile)

    final_sites = []
    map = dict()
    for each_dict in iso_data:
        map[each_dict["alpha2"]] = each_dict["numeric"]

    for each_country in lines:
        country = each_country.strip()
        if country in map:
            # print(each_country, map[country])
            final_sites.append(map[country])

    with open(json_res, 'w') as fp:
        json.dump(final_sites, fp)

    print(len(final_sites))

def country_converter():
    str = "Albania,Argentina,Australia,Austria,Belgium,Bosnia_And_Herzegovina,Brazil,Bulgaria,Canada,Chile,Colombia,Costa_Rica,Croatia,Cyprus,Czech_Republic,Denmark,Estonia,Finland,France,Georgia,Germany,Greece,Hong_Kong,Hungary,Iceland,Indonesia,Ireland,Israel,Italy,Japan,Latvia,Lithuania,Luxembourg,Malaysia,Mexico,Moldova,Netherlands,New_Zealand,North_Macedonia,Norway,Poland,Portugal,Romania,Serbia,Singapore,Slovakia,Slovenia,South_Africa,South_Korea,Spain,Sweden,Switzerland,Taiwan,Thailand,Turkey,Ukraine,United_Kingdom,United_States,Vietnam"
    strs = str.split(",")
    str_arr = []
    for each in strs:
        if "_" in each:
            each = each.replace("_", " ")
        if "And" in each:
            each = each.replace("And", "and")
        str_arr.append(each)

    print(str_arr)

    countries = {}
    # for country in pycountry.countries:
    #     countries[country.name] = country.alpha_2
    json_iso_path = f"{Path(__file__).parent.parent}/data/iso.json"
    with open(json_iso_path, mode="r") as jsonFile:
        countries_raw = json.load(jsonFile)

    for country in countries_raw:
        countries[country['name']] = country['alpha2']
        if 'altName' in country:
            countries[country['altName']] = country['alpha2']
        if 'shortName' in country:
            countries[country['shortName']] = country['alpha2']

    codes = [countries.get(country, 'Unknown code') for country in str_arr]

    print(codes, "len is: ", len(codes), "\n")  # prints ['AS', 'CA', 'FR']

    json_path = f"{Path(__file__).parent.parent}/data/countryList.txt"
    json_res = f"{Path(__file__).parent.parent}/data/vpn_country_map.json"

    with open(json_path, mode="r") as f:
        lines = f.readlines()

    total = {}
    matches = []
    unmatches = []
    for each_country in lines:
        country = each_country.strip()
        if country in codes:
            # print(country)
            matches.append(country)
        else:
            unmatches.append(country)

    total["matches"] = matches
    total["unmatches"] = unmatches

    with open(json_res, 'w') as fp:
        json.dump(total, fp)

    print(len(matches))

def count_site_for_each_country():
    json_path = f"{Path(__file__).parent.parent}/data/googleTop1000SitesCountries.json"
    json_res = f"{Path(__file__).parent.parent}/data/site_num_for_each_country.json"

    with open(json_path, mode="r") as jsonFile:
        google_sites = json.load(jsonFile)

    final_sites = {}

    for each_country, sites in google_sites.items():
        final_sites[each_country] = len(sites)

    with open(json_res, 'w') as fp:
        json.dump(final_sites, fp)


if __name__ == '__main__':
    # process_sites_file()
     country_converter()
    # count_site_for_each_country()
