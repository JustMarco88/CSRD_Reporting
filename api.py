from flask import Flask, jsonify, request
from main import get_vehicle_info

app = Flask(__name__)


@app.route('/enrich_data', methods=['GET'])
def enrich_data():
    kenteken = request.args.get('kenteken', '')

    if not kenteken:
        return jsonify({"error": "Kenteken parameter is missing"}), 400

    try:
        vehicle_info = get_vehicle_info(kenteken)

        if vehicle_info and 'co2_info' in vehicle_info:
            co2_info = vehicle_info['co2_info']
            co2_uitstoot_gecombineerd = co2_info.get('co2_uitstoot_gecombineerd', 0) if co2_info.get('brandstof_omschrijving') != "Elektriciteit" else 0
            return jsonify({"co2_uitstoot_gecombineerd": co2_uitstoot_gecombineerd})
        else:
            return jsonify({"error": "No CO2 information found for the provided Kenteken"}), 404

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
