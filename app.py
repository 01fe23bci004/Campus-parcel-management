from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = "parcels.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS parcels (
            parcel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            courier TEXT NOT NULL,
            tracking_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return jsonify({
        "service": "Parcel Service",
        "status": "running"
    })


@app.route("/parcels", methods=["POST"])
def create_parcel():

    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON data required"}), 400

    required_fields = [
        "student_id",
        "courier",
        "tracking_id",
        "status"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    try:
        conn = get_db_connection()

        cursor = conn.execute("""
            INSERT INTO parcels
            (student_id, courier, tracking_id, status)
            VALUES (?, ?, ?, ?)
        """, (
            data["student_id"],
            data["courier"],
            data["tracking_id"],
            data["status"]
        ))

        conn.commit()

        parcel_id = cursor.lastrowid

        conn.close()

        return jsonify({
            "parcel_id": parcel_id,
            "student_id": data["student_id"],
            "courier": data["courier"],
            "tracking_id": data["tracking_id"],
            "status": data["status"]
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Tracking ID already exists"
        }), 409


@app.route("/parcels", methods=["GET"])
def get_parcels():

    conn = get_db_connection()

    parcels = conn.execute(
        "SELECT * FROM parcels"
    ).fetchall()

    conn.close()

    return jsonify([
        dict(parcel) for parcel in parcels
    ])


@app.route("/parcels/<int:parcel_id>", methods=["GET"])
def get_parcel(parcel_id):

    conn = get_db_connection()

    parcel = conn.execute(
        "SELECT * FROM parcels WHERE parcel_id = ?",
        (parcel_id,)
    ).fetchone()

    conn.close()

    if parcel is None:
        return jsonify({
            "error": "Parcel not found"
        }), 404

    return jsonify(dict(parcel))


@app.route("/parcels/<int:parcel_id>", methods=["PUT"])
def update_parcel(parcel_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data required"
        }), 400

    conn = get_db_connection()

    parcel = conn.execute(
        "SELECT * FROM parcels WHERE parcel_id = ?",
        (parcel_id,)
    ).fetchone()

    if parcel is None:
        conn.close()

        return jsonify({
            "error": "Parcel not found"
        }), 404

    student_id = data.get("student_id", parcel["student_id"])
    courier = data.get("courier", parcel["courier"])
    tracking_id = data.get("tracking_id", parcel["tracking_id"])
    status = data.get("status", parcel["status"])

    try:

        conn.execute("""
            UPDATE parcels
            SET student_id = ?,
                courier = ?,
                tracking_id = ?,
                status = ?
            WHERE parcel_id = ?
        """, (
            student_id,
            courier,
            tracking_id,
            status,
            parcel_id
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "parcel_id": parcel_id,
            "student_id": student_id,
            "courier": courier,
            "tracking_id": tracking_id,
            "status": status
        })

    except sqlite3.IntegrityError:

        conn.close()

        return jsonify({
            "error": "Tracking ID already exists"
        }), 409


@app.route("/parcels/<int:parcel_id>", methods=["DELETE"])
def delete_parcel(parcel_id):

    conn = get_db_connection()

    parcel = conn.execute(
        "SELECT * FROM parcels WHERE parcel_id = ?",
        (parcel_id,)
    ).fetchone()

    if parcel is None:
        conn.close()

        return jsonify({
            "error": "Parcel not found"
        }), 404

    conn.execute(
        "DELETE FROM parcels WHERE parcel_id = ?",
        (parcel_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Parcel deleted successfully"
    })


if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
