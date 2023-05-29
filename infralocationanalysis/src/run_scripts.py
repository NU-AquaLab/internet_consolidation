import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import dnsCentralization
import dao.dns_db_model as dns_db_model
from github_config import git_upload_file
from dnsAnalysisTool import plotDNSPlots

if __name__ == "__main__":
    country_code = sys.argv[1]

    if country_code is None:
        country_code = 'US'
    logging.info("country_code is:", country_code)
    aggregated_dns_results = dnsCentralization.start_dns(country_code)

    dns_file_name = "dns_centralization_" + country_code + ".json"
    dns_src_file_path = f"{Path(__file__).parent.parent}/results/" + dns_file_name

    with open(dns_src_file_path, 'w') as fp:
        json.dump(aggregated_dns_results, fp)

    git_upload_file("dns/" + dns_file_name, dns_src_file_path)
    logging.info("upload dns data successfully in country: ", country_code)

    # analyze dns_centralization file
    dnsResults = json.load(open(dns_src_file_path))
    aggregated_dns_analysis = plotDNSPlots(dnsResults, country_code)

    dns_analysis_file_name = "dns_centralization_analysis" + country_code + ".json"
    dns_analysis_src_file_path = f"{Path(__file__).parent.parent}/results/" + dns_analysis_file_name

    with open(dns_analysis_src_file_path, 'w') as fp:
        json.dump(aggregated_dns_analysis, fp)

    git_upload_file("dns/" + dns_analysis_file_name, dns_analysis_src_file_path)
    logging.info("upload dns data successfully in country: ", country_code)

    current_year = datetime.now().year
    # write analysis data into database
    dns_db_model.insert_table_dns_analysis(aggregated_dns_analysis, current_year)