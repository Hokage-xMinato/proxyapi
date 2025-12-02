import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Configuration Section: Define your custom API endpoints here ---
# The key is the unique ID you will use in the URL (e.g., /api?get=10Aarambh)
API_CONFIGS = {
    "10Aarambh": {
        "url": "https://theeduverse.xyz/api/eduverse/api/10",
        "referrer": "https://theeduverse.xyz/courses/10th/details",
        "description": "API for 10th grade content details."
    },
    "11PrarambhPCMB": {
        "url": "https://theeduverse.xyz/api/eduverse/api/11/science",
        "referrer": "https://theeduverse.xyz/courses/11th/details-science",
        "description": "Internal API call for active user list."
    },
    "10Abhay": {
        "url": "https://e-leak.vercel.app/api/batches/39904"
        "referrer": "https://e-leak.vercel.app/courses/details/39904"
        "description": "10 Abhay batch"
    }
    # Add as many more configurations as you need
    # "YourCustomID": {
    #     "url": "https://your.target.api/endpoint",
    #     "referrer": "https://your.internal.referer.domain",
    #     "description": "Description of this proxied API."
    # }
}
# -------------------------------------------------------------------

# --- Flask Server Setup ---
PORT = int(os.environ.get('PORT', 5000))
app = Flask(__name__)
# Enable CORS for the frontend (especially important if running frontend/backend separately)
CORS(app) 

@app.route('/api', methods=['GET'])
def proxy_request():
    """
    Looks up the configuration ID from the 'get' query parameter, executes the 
    external GET request with hidden headers, and returns the result.
    """
    config_id = request.args.get('get')

    if not config_id:
        return jsonify({
            "error": "Missing 'get' parameter.",
            "message": "Please use the format: /api?get=<ConfigurationID>"
        }), 400

    config = API_CONFIGS.get(config_id)

    if not config:
        return jsonify({
            "error": "Invalid Configuration ID.",
            "message": f"ID '{config_id}' not found in server configuration."
        }), 404
        
    target_url = config['url']
    referrer = config['referrer']
    
    # Define the hardcoded, specific headers for the external request
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
        "sec-ch-ua": '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "Accept": "*/*",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "Referer": referrer, 
        "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
    }
    
    try:
        # Perform the internal request
        response = requests.get(target_url, headers=headers, timeout=10)

        response_data = {
            "config_id": config_id,
            "status_code": response.status_code,
            "content_encoding": response.headers.get("Content-Encoding"),
            "data": None # Placeholder for the actual content
        }
        
        # Try to parse as JSON first, if not, send raw text
        try:
            response_data["data"] = response.json()
        except requests.exceptions.JSONDecodeError:
            response_data["data"] = response.text
            
        # Return the proxy result to the client
        return jsonify(response_data), 200

    except requests.exceptions.RequestException as e:
        print(f"Error making external request for ID {config_id}: {e}")
        return jsonify({
            "config_id": config_id,
            "error": "Failed to connect to the external API.", 
            "details": str(e)
        }), 502 

    except Exception as e:
        print(f"An unexpected error occurred for ID {config_id}: {e}")
        return jsonify({"error": "An unexpected error occurred on the server.", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
