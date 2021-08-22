
import Algorithmia
import os
import pandas as pd
from pandas.core.frame import DataFrame
from datetime import datetime, time
from joblib import load
import numpy as np

MY_API_KEY = os.getenv("ALGO_API_KEY_POC", None)
ALGORITHMIA_API = os.getenv('ALGO_API_ADDRESS_POC', None)

client = Algorithmia.client(MY_API_KEY, ALGORITHMIA_API)

# Model version A - Gradient boosting classifier
model = load(client.file(
    "data://zma/credit_card_approval/model-a.joblib").getFile().name)


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages


def apply(input):

    batch_input = pd.read_csv(
        client.file(input).getFile().name
    )

    # print(batch_input.shape)

    records = batch_input.to_dict("records")

    decisions = []
    count = 0
    start_time = datetime.now()

    for record in records:
        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H:%M:%S.%f")[:-3]
        timestamp_dict = {"timestamp": timestamp}

        ###########################################################
        # Inference on risk score and make decision on approval #
        ###########################################################
        params = preprocessing_input(record)
        risk_score = model.predict_proba(params)
        risk_score = round(float(risk_score[0][1]), 2)
        approved = int(1 - model.predict(params)[0])

        result = {"risk_score": risk_score, "approved": approved}

        results = dict(record, **result, **timestamp_dict)
        # print(str(results))

        decisions.append(results)
        count += 1
        # print(str(count))

        if count > 30000:
            break

    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()

    ############################################################################
    # Store batch processing outcome to a csv file in the hosted data storage. #
    ############################################################################
    output_file_name = "credit_card_applications_decisions_" + \
        str(timestamp) + ".csv"
    DataFrame.from_dict(decisions).to_csv(output_file_name)

    output_dictory_path = "data://zma/credit_card_approval/"

    output_file_path = output_dictory_path + output_file_name
    client.file(output_file_path).putFile(output_file_name)

    # client.report_insights({"batch.number_of_record": count})

    return {
        "record_processed": count,
        "start time": start_time.strftime(
            "%Y-%m-%d_%H:%M:%S.%f")[:-3],
        "completion time": end_time.strftime(
            "%Y-%m-%d_%H:%M:%S.%f")[:-3],
        "duration": duration,
        "output path": output_file_path
    }


def preprocessing_input(input):
    ##########################
    # Processing input data #
    ##########################
    params = np.array(
        [
            input.get("high_balance", 0),
            input.get("owns_home", 1),
            input.get("child_one", 0),
            input.get("child_two_plus", 0),
            input.get("has_work_phone", 0),
            input.get("age_high", 0),
            input.get("age_highest", 1),
            input.get("age_low", 0),
            input.get("age_lowest", 0),
            input.get("employment_duration_high", 0),
            input.get("employment_duration_highest", 0),
            input.get("employment_duration_low", 0),
            input.get("employment_duration_medium", 0),
            input.get("occupation_hightech", 0),
            input.get("occupation_office", 1),
            input.get("family_size_one", 1),
            input.get("family_size_three_plus", 0),
            input.get("housing_coop_apartment", 0),
            input.get("housing_municipal_apartment", 0),
            input.get("housing_office_apartment", 0),
            input.get("housing_rented_apartment", 0),
            input.get("housing_with_parents", 0),
            input.get("education_higher_education", 0),
            input.get("education_incomplete_higher", 0),
            input.get("education_lower_secondary", 0),
            input.get("marital_civil_marriage", 0),
            input.get("marital_separated", 0),
            input.get("marital_single_not_married", 1),
            input.get("marital_widow", 0),
        ]
    ).reshape(1, -1)

    return params


if __name__ == "__main__":
    input = "data://demo/credit_card_approval_batch/credit_card_applications.csv"
    apply(input)
