import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Configuration Section ---
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
        "url": "https://theeduverse.xyz/api/batches/39904",
        "referrer": "https://theeduverse.xyz/courses/details/39904",
        "description": "10 Abhay batch"
    },
    "10Abhay": {
        "url": "https://theeduverse.xyz/api/39904",
        "referrer": "https://theeduverse.xyz",
        "description": "Description of this proxied API."
    },
    "11NirbhayBatch": {
        "url": "https://theeduverse.xyz/api/batches/40688",
        "referrer": "https://theeduverse.xyz",
        "description": "Description of this proxied API."
    },
    "11Nirbhay": {
        "url": "https://theeduverse.xyz/api/40688",
        "referrer": "https://theeduverse.xyz",
        "description": "Description of this proxied API."
    }
}

# --- Flask Server Setup ---
PORT = int(os.environ.get('PORT', 5000))
app = Flask(__name__)
CORS(app) 

# Base set of spoofed headers used for all proxy requests
BASE_HEADERS = {
    "sec-ch-ua-platform": '"Windows"',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    "sec-ch-ua": '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "Accept": "*/*",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
    
    # --- Added Custom Headers ---
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjbGllbnRJZCI6IjA5MjBhODBkMGJmNjM5NTdhNzVhNmM5OTNiN2VmNjk4YTYyZjAwOWMxYjY3OTA4ZmY2ZWI4M2ZiNmY2NGMyMjkiLCJpYXQiOjE3Njg0ODI4MzUsImV4cCI6MTc2ODUwNDQzNX0.dDlY6Gy2NlJYC1d4CcbVqMBZxoYX3tMkpXGbqVJNqvo",
    "client-id": "0920a80d0bf63957a75a6c993b7ef698a62f009c1b67908ff6eb83fb6f64c229"
}

def _make_external_request(target_url, referrer, client_params):
    headers = BASE_HEADERS.copy()
    headers["Referer"] = referrer 
    
    try:
        response = requests.get(target_url, headers=headers, timeout=10, params=client_params)
        result = {
            "status_code": response.status_code,
            "content_encoding": response.headers.get("Content-Encoding"),
            "data": None 
        }
        
        try:
            result["data"] = response.json()
        except requests.exceptions.JSONDecodeError:
            result["data"] = response.text
            
        return result, 200

    except requests.exceptions.RequestException as e:
        return {"error": "Connection failed", "details": str(e)}, 502
    except Exception as e:
        return {"error": "Server error", "details": str(e)}, 500


@app.route('/', methods=['GET'])
def list_configs():
    available_configs = {k: {"description": v["description"], "example_url": f"/api?get={k}"} for k, v in API_CONFIGS.items()}
    return jsonify({
        "message": "API Proxy Server Active.",
        "available_endpoints": available_configs
    }), 200


@app.route('/api', methods=['GET'])
def proxy_request():
    config_id = request.args.get('get')
    path_suffix = request.args.get('path')

    if not config_id:
        return jsonify({"error": "Missing 'get' parameter."}), 400

    config = API_CONFIGS.get(config_id)
    if not config:
        return jsonify({"error": "Invalid Configuration ID."}), 404
        
    target_url = config['url']
    referrer = config['referrer']

    if path_suffix:
        if not target_url.endswith('/') and not path_suffix.startswith('/'):
            target_url += '/'
        target_url += path_suffix
    
    client_params = {k: v for k, v in request.args.items() if k not in ['get', 'path']}
    result, status_code = _make_external_request(target_url, referrer, client_params)

    result["config_id"] = config_id
    result["target_url_used"] = target_url
    
    return jsonify(result), status_code

@app.route('/test', methods=['GET'])
def test_request():
    target_url = request.args.get('url')
    referrer = request.args.get('referrer')
    path_suffix = request.args.get('path')

    if not target_url or not referrer:
        return jsonify({"error": "Missing url or referrer."}), 400

    if path_suffix:
        if not target_url.endswith('/') and not path_suffix.startswith('/'):
            target_url += '/'
        target_url += path_suffix

    client_params = {k: v for k, v in request.args.items() if k not in ['url', 'referrer', 'path']}
    result, status_code = _make_external_request(target_url, referrer, client_params)
    
    result["test_mode"] = True
    result["target_url_used"] = target_url
    
    return jsonify(result), status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
