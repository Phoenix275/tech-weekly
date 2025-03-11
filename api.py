from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/update', methods=['GET'])
def update_content():
    """Runs the Python script to generate new content and updates the website."""
    try:
        result = subprocess.run(["python3", "tech_weekly.py"], capture_output=True, text=True)
        return jsonify({"status": "success", "output": result.stdout}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
