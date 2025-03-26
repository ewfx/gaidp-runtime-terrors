import json

import pandas as pd

from langchain.llms import OpenAI

from langchain.prompts import PromptTemplate

import streamlit as st

 

# Load metadata

def load_metadata(metadata_file):

    with open(metadata_file, "r") as f:

        return json.load(f)

 

# Load data from different file formats

def load_data(file_path):

    if file_path.endswith(".csv"):

        return pd.read_csv(file_path)

    elif file_path.endswith(".xlsx"):

        return pd.read_excel(file_path)

    elif file_path.endswith(".json"):

        return pd.read_json(file_path)

    else:

        raise ValueError("Unsupported file format.")

 

# Validate rows based on metadata

def validate_row(row, metadata):

    errors = []

    for column, config in metadata["columns"].items():

        if column not in row:

            continue  # Skip if column is missing

        if config["validation"] == "non_negative" and row[column] < 0:

            errors.append(f"{column} cannot be negative.")

        if config["validation"] == "match_reported_amount" and not is_match_with_deviation(row['Transaction_Amount'], row['Reported_Amount']):

            errors.append("Transaction_Amount does not match Reported_Amount.")

        if config["validation"] == "valid_currency" and not is_valid_currency(row[column]):

            errors.append(f"Invalid currency code: {row[column]}.")

        if config["validation"] == "not_future" and pd.to_datetime(row[column]) > pd.Timestamp.now():

            errors.append(f"{column} cannot be in the future.")

    return errors

 

# Helper functions

def is_match_with_deviation(amount1, amount2, deviation=0.01):

    return abs(amount1 - amount2) <= amount1 * deviation

 

def is_valid_currency(currency):

    valid_currencies = ["USD", "EUR", "GBP"]

    return currency in valid_currencies

 

# Calculate risk scores

def calculate_risk_score(row):

    risk_score = 0

    if len(row['errors']) > 0:

        risk_score += 5

    if row['Transaction_Amount'] > 5000:

        risk_score += 3

    if is_high_risk_country(row['Country']):

        risk_score += 2

    if is_round_number(row['Transaction_Amount']):

        risk_score += 1

    return risk_score

 

def is_high_risk_country(country):

    high_risk_countries = ["DE", "UK"]

    return country in high_risk_countries

 

def is_round_number(amount):

    return amount % 1000 == 0

 

# Add new column with metadata

def add_new_column(data, column_name, column_type, validation_rule, metadata):

    if column_name not in metadata["columns"]:

        metadata["columns"][column_name] = {"type": column_type, "validation": validation_rule}

        with open("metadata.json", "w") as f:

            json.dump(metadata, f, indent=4)

    else:

        print(f"Column {column_name} already exists.")

 

# Streamlit app

def main():

    st.title("Regulatory Compliance Assistant")

 

    # Upload metadata file

    metadata_file = st.file_uploader("Upload metadata file (JSON):", type=["json"])

    if metadata_file:

        metadata = load_metadata(metadata_file)

        st.write("Metadata:", metadata)

 

        # Upload transaction data

        data_file = st.file_uploader("Upload transaction data (CSV, Excel, JSON):", type=["csv", "xlsx", "json"])

        if data_file:

            data = load_data(data_file)

            st.write("Data Preview:", data.head())

 

            # Run validation

            if st.button("Validate Data"):

                data['errors'] = data.apply(lambda row: validate_row(row, metadata), axis=1)

                flagged_transactions = data[data['errors'].apply(len) > 0]

                st.write("Flagged Transactions:", flagged_transactions)

 

                # Calculate risk scores

                data['risk_score'] = data.apply(calculate_risk_score, axis=1)

                st.write("Risk Scores:", data[['Transaction_ID', 'risk_score']])

 

                # Generate remediation suggestions

                llm = OpenAI(api_key="your_openai_api_key", model="gpt-3.5-turbo")

                for _, row in flagged_transactions.iterrows():

                    remediation = llm(f"Suggest remediation for transaction {row['Transaction_ID']} with errors: {row['errors']}")

                    st.write(f"Transaction {row['Transaction_ID']}: {remediation}")

 

            # Add new column

            st.subheader("Add New Column")

            new_column_name = st.text_input("Enter new column name:")

            new_column_type = st.selectbox("Select column type:", ["int", "float", "string", "date"])

            new_column_validation = st.text_input("Enter validation rule:")

            if st.button("Add New Column"):

                add_new_column(data, new_column_name, new_column_type, new_column_validation, metadata)

                st.write(f"Added new column: {new_column_name}")

 

if __name__ == "__main__":

    main()