import Algorithmia
import os
import numpy as np
from joblib import load

ALGORITHMIA_API_KEY = os.getenv("ALGORITHMIA_API_KEY", None)
ALGORITHMIA_API = os.getenv("ALGORITHMIA_API", None)
client = Algorithmia.client(ALGORITHMIA_API_KEY, ALGORITHMIA_API)

# client = Algorithmia.client()

# Model version A - Gradient boosting classified
model = load(client.file(
    "data://zma/credit_card_approval/model-a.joblib").getFile().name)


# Model version B - Random forest classifier
# model = load(client.file("data://algorithmia_se/CreditCardApproval/model-b.joblib").getFile().name)


def apply(input):
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

    risk_score = model.predict_proba(params)
    risk_score = round(float(risk_score[0][1]), 2)
    approved = int(1 - model.predict(params)[0])
    return {"risk_score": risk_score, "approved": approved}
