import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

import cdnCentralization
import dao.cdn_db_model as cdn_db_model
from github_config import git_upload_file
from cdnAnalysisTool import run_analysis

if __name__ == "__main__":
    country_code = sys.argv[1]

    if country_code is None:
        country_code = 'US'
    logging.info("country_code is:", country_code)
    if not os.path.exists("../results"):
        os.mkdir("../results")
    aggregated_cdn_results = cdnCentralization.runProgram(country_code)
    cdn_file_name = "cdn_centralization_"+country_code+".json"
    cdn_src_file_path = f"{Path(__file__).parent.parent}/results/"+cdn_file_name

    with open(cdn_src_file_path, 'w') as fp:
        json.dump(aggregated_cdn_results, fp)

    git_upload_file("cdn/"+cdn_file_name, cdn_src_file_path)
    logging.info("upload cdn data successfully in country: ", country_code)

    # analyze dns_centralization file
    aggregated_cdn_analysis = run_analysis(country_code)

    cdn_analysis_file_name = "cdn_centralization_analysis" + country_code + ".json"
    cdn_analysis_src_file_path = f"{Path(__file__).parent.parent}/results/" + cdn_analysis_file_name

    with open(cdn_analysis_src_file_path, 'w') as fp:
        json.dump(aggregated_cdn_analysis, fp)

    git_upload_file("cdn/"+cdn_analysis_file_name, cdn_analysis_src_file_path)
    logging.info("upload cdn data successfully in country: ", country_code)

    current_year = datetime.now().year
    # write analysis data into database
    cdn_db_model.insert_table_cdn_analysis(aggregated_cdn_analysis, current_year)