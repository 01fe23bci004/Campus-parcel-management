from flask import Flask, request, jsonify
import json
import sqlite3

app = Flask(__name__)

DATABASE = "pickups.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pickups (
            pickup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            parcel_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# POST /pickup
@app.route("/pickup", methods=["POST"])
def create_pickup():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    if "parcel_id" not in data or "student_id" not in data:
        return jsonify({
            "error": "parcel_id and student_id are required"
        }), 400
   
    # verify parcel through parcel services
    
    try: 
        import urllib.request

        parcel_url = f"http://parcel-service:8000/parcels/{data['parcel_id']}"
        with urllib.request.urlopen(parcel_url, timeout=5) as response:
            parcel_data = json.loads(response.read().decode())

    except Exception:
        return jsonify({
            "error": "Parcel Service could not verify the parcel"
        }), 404

    # Verify student through Student Service
    try:
        student_url = f"http://student-service:8000/students/{data['student_id']}"
        with urllib.request.urlopen(student_url, timeout=5) as response:
            student_data = json.loads(response.read().decode())

    except Exception:
        return jsonify({
            "error": "Student Service could not verify the student"
        }), 404

    conn = get_db_connection()

    cursor = conn.execute(
        """
        INSERT INTO pickups
        (parcel_id, student_id, status)
        VALUES (?, ?, ?)
        """,
        (
            data["parcel_id"],
            data["student_id"],
            "PENDING"
        )
    )

    conn.commit()

    pickup_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "pickup_id": pickup_id,
        "parcel_id": data["parcel_id"],
        "student_id": data["student_id"],
        "status": "PENDING"
    }), 201


# GET /pickup
@app.route("/pickup", methods=["GET"])
def get_pickups():

    conn = get_db_connection()

    pickups = conn.execute(
        "SELECT * FROM pickups"
    ).fetchall()

    conn.close()

    result = []

    for pickup in pickups:
        result.append({
            "pickup_id": pickup["pickup_id"],
            "parcel_id": pickup["parcel_id"],
            "student_id": pickup["student_id"],
            "status": pickup["status"]
        })

    return jsonify(result), 200


# GET /pickup/{pickup_id}
@app.route("/pickup/<int:pickup_id>", methods=["GET"])
def get_pickup(pickup_id):

    conn = get_db_connection()

    pickup = conn.execute(
        "SELECT * FROM pickups WHERE pickup_id = ?",
        (pickup_id,)
    ).fetchone()

    conn.close()

    if pickup is None:
        return jsonify({
            "error": "Pickup not found"
        }), 404

    return jsonify({
        "pickup_id": pickup["pickup_id"],
        "parcel_id": pickup["parcel_id"],
        "student_id": pickup["student_id"],
        "status": pickup["status"]
    }), 200


# PUT /pickup/{pickup_id}/complete
@app.route("/pickup/<int:pickup_id>/complete", methods=["PUT"])
def complete_pickup(pickup_id):

    conn = get_db_connection()

    pickup = conn.execute(
        "SELECT * FROM pickups WHERE pickup_id = ?",
        (pickup_id,)
    ).fetchone()

    if pickup is None:
        conn.close()

        return jsonify({
            "error": "Pickup not found"
        }), 404

    conn.execute(
        """
        UPDATE pickups
        SET status = ?
        WHERE pickup_id = ?
        """,
        ("COMPLETED", pickup_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "pickup_id": pickup_id,
        "parcel_id": pickup["parcel_id"],
        "student_id": pickup["student_id"],
        "status": "COMPLETED"
    }), 200


@app.route("/")
def home():
    return jsonify({
        "service": "Campus Pickup Service",
        "status": "running"
    })


if __name__ == "__main__":
    init_db()

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )
