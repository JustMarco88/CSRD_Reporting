import pandas as pd
import requests
import streamlit as st


def sanitize_kenteken(input_str):
    return ''.join(char.upper() for char in input_str if char.isalnum())


def get_info(url, kenteken):
    filtered_url = f"{url}?$filter=kenteken eq '{kenteken}'"

    response = requests.get(filtered_url)

    if response.status_code == 200:
        data = response.json()

        if 'value' in data and len(data['value']) > 0:
            return data['value'][0]
        else:
            return None
    else:
        return None


def get_vehicle_info(kenteken):
    co2_url = "https://opendata.rdw.nl/api/odata/v4/8ys7-d773"
    general_url = "https://opendata.rdw.nl/api/odata/v4/m9d7-ebf2"

    co2_info = get_info(co2_url, kenteken)
    general_info = get_info(general_url, kenteken)

    return {"co2_info": co2_info,
            "general_info": general_info}


def input_tab():
    st.title("Voertuig informatie - Manual Input")

    with st.form("voertuig_info_form"):
        kenteken_input = st.text_input("Kenteken:")
        sanitized_kenteken = sanitize_kenteken(kenteken_input)
        zoek_button = st.form_submit_button("Zoek")

    if zoek_button:
        if sanitized_kenteken:
            vehicle_data = get_vehicle_info(sanitized_kenteken)

            if vehicle_data:
                co2_uitstoot_gecombineerd = vehicle_data.get('co2_uitstoot_gecombineerd', 'N/A')
                st.subheader(f"Voertuig gegevens voor kenteken: {sanitized_kenteken}")
                st.write(f"CO2 uitstoot (gecombineerd): {co2_uitstoot_gecombineerd} g/km")
                st.json(vehicle_data)
            else:
                st.warning(f"Geen informatie gevonden voor Kenteken: {sanitized_kenteken}")
        else:
            st.warning("Vul een juist kenteken in.")


def enrich_data_with_co2(df):
    enriched_data = []

    for index, row in df.iterrows():
        kenteken = row['Kenteken']
        unique_id = row['unique_id']  # Assuming 'unique_id' is a column in your CSV

        vehicle_data = get_vehicle_info(kenteken)

        co2_uitstoot_gecombineerd = vehicle_data['co2_info']['co2_uitstoot_gecombineerd']
        if vehicle_data['co2_info']['brandstof_omschrijving'] == "Elektriciteit":
            row['CO2_uitstoot_gecombineerd'] = 0
            row['brandstof_omschrijving'] = vehicle_data['co2_info']['brandstof_omschrijving']
        else:
            row['CO2_uitstoot_gecombineerd'] = co2_uitstoot_gecombineerd
            row['brandstof_omschrijving'] = vehicle_data['co2_info']['brandstof_omschrijving']

        # Include 'unique_id' in the enriched data
        row['unique_id'] = unique_id

        # Include only the necessary columns in the result
        result_row = row[['unique_id', 'CO2_uitstoot_gecombineerd', 'brandstof_omschrijving']]
        enriched_data.append(result_row)

    return pd.DataFrame(enriched_data)


def csv_tab():
    st.title("Voertuig informatie - CSV Upload")
    st.caption("Het CSV bestand moet de kolommen 'unique_id' en 'Kenteken' bevatten. We verrijken het bestand door "
               "extra informatie toe te voegen, maar retourneren het zonder de 'Kenteken'-gegevens. We slaan geen "
               "informatie op en gebruiken het kenteken slechts één keer om de gegevens te verrijken.")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file is not None:
        try:

            potential_delimiters = [',', ';', '\t']

            for delimiter in potential_delimiters:
                try:

                    df = pd.read_csv(uploaded_file, delimiter=delimiter)
                    required_columns = ['Kenteken', 'unique_id']

                    if not all(col in df.columns for col in required_columns):
                        st.warning(f"CSV file must contain {', '.join(required_columns)} columns.")
                        return

                    df['Kenteken'] = df['Kenteken'].apply(sanitize_kenteken)
                    enriched_df = enrich_data_with_co2(df)

                    st.subheader("Enriched Data:")
                    st.write(enriched_df)

                    enriched_csv = enriched_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=enriched_csv,
                        file_name="enriched_data.csv",
                        key="download_button"
                    )

                    break

                except pd.errors.ParserError:
                    continue

        except pd.errors.EmptyDataError:
            st.warning("The uploaded CSV file is empty.")


def main():
    tabs = ["Query", "CSV Upload"]
    selected_tab = st.sidebar.radio("Options:", tabs)

    if selected_tab == "Query":
        input_tab()
    elif selected_tab == "CSV Upload":
        csv_tab()


if __name__ == "__main__":
    main()
