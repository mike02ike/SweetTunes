from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def start():
    return jsonify({"message": "Sweet Tunes backend running!"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    return jsonify({"message": "Lets log in!"})

@app.route('/logout')
def logout():
    #logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)