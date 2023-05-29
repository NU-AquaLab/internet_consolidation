import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import caCentralization
import dao.ca_db_model as ca_db_model
from github_config import git_upload_file
from caAnalysisTool import collectResults

if __name__ == "__main__":
    country_code = sys.argv[1]

    if country_code is None:
        country_code = 'US'
    logging.info("country_code is:", country_code)
    aggregated_ca_results = caCentralization.runProgram(country_code)
    ca_file_name = "ca_centralization_"+country_code+".json"
    ca_src_file_path = f"{Path(__file__).parent.parent}/results/"+ca_file_name

    with open(ca_src_file_path, 'w') as fp:
        json.dump(aggregated_ca_results, fp)

    git_upload_file("ca/"+ca_file_name, ca_src_file_path)
    logging.info("upload ca data successfully in country: ", country_code)

    # analyze dns_centralization file
    ca_results = json.load(open(ca_src_file_path))
    aggregated_ca_analysis = collectResults(ca_results)

    ca_analysis_file_name = "ca_centralization_analysis" + country_code + ".json"
    ca_analysis_src_file_path = f"{Path(__file__).parent.parent}/results/" + ca_analysis_file_name

    with open(ca_analysis_src_file_path, 'w') as fp:
        json.dump(aggregated_ca_analysis, fp)

    git_upload_file("ca/"+ca_analysis_file_name, ca_analysis_src_file_path)
    logging.info("upload ca data successfully in country: ", country_code)

    current_year = datetime.now().year
    # write analysis data into database
    ca_db_model.insert_table_ca_analysis(aggregated_ca_analysis, current_year)