import base64
import io
import os
from flask import Flask, request, jsonify
import requests
from pdf2image import convert_from_bytes
from tempfile import TemporaryDirectory
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from geopy.distance import geodesic
import json

app = Flask(__name__)



@app.route('/pdf-to-image', methods=['POST'])
def pdf_to_image():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Fetch the PDF file
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        pdf_data = response.content

        # Convert PDF to images
        images = convert_from_bytes(pdf_data, fmt='jpeg')

        # Convert images to base64
        base64_images = []
        for img in images:
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue())
            base64_images.append(img_str.decode('utf-8'))

        return jsonify({'message': 'Images converted to base64 successfully', 'images': base64_images})

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to process PDF'}), 500

# Function to check if a location is within 50 km of the central point
def is_within_radius(lat, lon, center, radius=50):
    return geodesic((float(lat), float(lon)), center).kilometers <= radius

@app.route('/within-radius', methods=['POST'])
def within_radius():
    try:
        central_point = request.json.get('central_point')
        radius = request.json.get('radius')
        data = request.json.get('data')
        new_data = []
        for coordinate in data:
            try:
                if coordinate.get("longitude") and coordinate.get("latitude") and is_within_radius(coordinate.get("latitude"), coordinate.get("longitude"), (central_point.get('latitude'), central_point.get('longitude')), radius):
                    new_data.append(coordinate)
            except Exception as e:
                print(coordinate, e)
        return jsonify({'message': 'Data calculated successfully', 'data': new_data})
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to calculate within radius.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
