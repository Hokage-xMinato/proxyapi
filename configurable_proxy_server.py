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
    "10AbhayBatch": {
        "url": "https://e-leak.vercel.app/api/batches/39904",
        "referrer": "https://e-leak.vercel.app/courses/details/39904",
        "description": "10 Abhay batch"
    },
    "10Abhay": {
        "url": "https://e-leak.vercel.app/api/39904",
        "referrer": "https://e-leak.vercel.app",
        "description": "Description of this proxied API."
    },
    "11NirbhayBatch": {
        "url": "https://e-leak.vercel.app/api/batches/40688",
        "referrer": "https://e-leak.vercel.app",
        "description": "Description of this proxied API."
    },
    "11Nirbhay": {
        "url": "https://e-leak.vercel.app/api/40688",
        "referrer": "https://e-leak.vercel.app",
        "description": "Description of this proxied API."
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

# Base set of spoofed headers used for all proxy requests
BASE_HEADERS = {
    # Standard browser fingerprinting headers
    "sec-ch-ua-platform": '"Windows"',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    "sec-ch-ua": '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    
    # Request metadata headers
    "Accept": "*/*",
    "sec-fetch-site": "same-origin", # Often a critical header for some servers
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    
    # Accept Language
    "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
}

def _make_external_request(target_url, referrer, client_params):
    """
    Internal utility function to handle the actual request logic,
    shared by both /api and /test endpoints.
    """
    # Create the final headers dictionary by copying BASE_HEADERS and adding the referrer
    headers = BASE_HEADERS.copy()
    # The critical header for bypassing referer-based security checks
    headers["Referer"] = referrer 
    
    try:
        # Perform the internal request with a timeout and forward remaining query parameters
        response = requests.get(target_url, headers=headers, timeout=10, params=client_params)

        result = {
            "status_code": response.status_code,
            "content_encoding": response.headers.get("Content-Encoding"),
            "data": None 
        }
        
        # Try to parse as JSON first. If it fails, treat it as raw text.
        try:
            result["data"] = response.json()
        except requests.exceptions.JSONDecodeError:
            result["data"] = response.text
            
        return result, 200

    except requests.exceptions.RequestException as e:
        # Handles connection issues, timeouts, DNS errors, etc.
        print(f"Error making external request to {target_url}: {e}")
        return {
            "error": "Failed to connect to the external API or request timed out.", 
            "details": str(e)
        }, 502 # Bad Gateway

    except Exception as e:
        # Catches any other unexpected server errors
        print(f"An unexpected error occurred for target {target_url}: {e}")
        return {"error": "An unexpected server error occurred.", "details": str(e)}, 500


@app.route('/', methods=['GET'])
def list_configs():
    """
    Returns a list of all configured API IDs and their descriptions for easy reference.
    """
    available_configs = {}
    for key, value in API_CONFIGS.items():
        available_configs[key] = {
            "description": value["description"],
            "example_url": f"/api?get={key}"
        }
    return jsonify({
        "message": "Welcome to the API Proxy Server.",
        "instructions": "Use the /api endpoint for predefined configs or the /test endpoint for custom URLs.",
        "api_endpoint_usage": "URL: /api?get=<ConfigID>[&path=<optional/path/suffix>][&param=value]",
        "test_endpoint_usage": "URL: /test?url=<TargetURL>&referrer=<CustomReferrer>[&path=<optional/path/suffix>][&param=value]",
        "available_endpoints": available_configs
    }), 200


@app.route('/api', methods=['GET'])
def proxy_request():
    """
    Looks up the configuration ID from the 'get' query parameter, executes the 
    external GET request with hidden headers, and returns the result.
    It supports an optional 'path' query parameter to append to the target URL.
    """
    config_id = request.args.get('get')
    path_suffix = request.args.get('path')

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

    # --- Append path suffix to the target URL ---
    if path_suffix:
        # Ensures correct slash usage when concatenating the base URL and the path suffix
        if not target_url.endswith('/') and not path_suffix.startswith('/'):
            target_url += '/'
        target_url += path_suffix
    # -------------------------------------------------------------------
    
    # Extract all client query parameters except those used for configuration
    client_params = {k: v for k, v in request.args.items() if k not in ['get', 'path']}
    
    result, status_code = _make_external_request(target_url, referrer, client_params)

    # Augment the result with configuration-specific details
    result["config_id"] = config_id
    result["target_url_used"] = target_url
    
    return jsonify(result), 200 # Note: _make_external_request returns 200 for success and 502/500 for failures

@app.route('/test', methods=['GET'])
def test_request():
    """
    Allows temporary testing against a custom URL and custom referrer provided
    via query parameters.
    """
    target_url = request.args.get('url')
    referrer = request.args.get('referrer')
    path_suffix = request.args.get('path')

    if not target_url or not referrer:
        return jsonify({
            "error": "Missing required parameters.",
            "message": "Please use the format: /test?url=<TargetURL>&referrer=<CustomReferrer>[&path=<optional/path/suffix>][&param=value]"
        }), 400

    # --- Append path suffix to the target URL ---
    if path_suffix:
        # Ensures correct slash usage when concatenating the base URL and the path suffix
        if not target_url.endswith('/') and not path_suffix.startswith('/'):
            target_url += '/'
        target_url += path_suffix
    # -------------------------------------------------------------------

    # Extract all client query parameters except those used for configuration
    client_params = {k: v for k, v in request.args.items() if k not in ['url', 'referrer', 'path']}

    result, status_code = _make_external_request(target_url, referrer, client_params)
    
    # Augment the result with the test parameters used
    result["test_mode"] = True
    result["target_url_used"] = target_url
    result["referrer_used"] = referrer
    
    return jsonify(result), status_code


if __name__ == '__main__':
    # Running in debug mode is useful for development but should be disabled in production
    app.run(host='0.0.0.0', port=PORT, debug=True)
