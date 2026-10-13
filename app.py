from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json

from config import SECRET_KEY
from services.database import init_database, get_user_by_username, get_db_connection
from services.image_processor import analyze_strip


app = Flask(__name__)

app.secret_key = SECRET_KEY


# Initialize database
init_database()


# =========================
# HOME
# =========================

@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] == "manager":
        return redirect(url_for("manager_dashboard"))

    return redirect(url_for("worker_dashboard"))


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        user = get_user_by_username(username)

        if user:

            from werkzeug.security import check_password_hash

            if check_password_hash(user["password"], password):

                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["name"] = user["name"]
                session["role"] = user["role"]

                if user["role"] == "manager":
                    return redirect(url_for("manager_dashboard"))

                return redirect(url_for("worker_dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# WORKER DASHBOARD
# =========================

@app.route("/worker-dashboard")
def worker_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only workers can access this page
    if session["role"] != "worker":
        return redirect(url_for("manager_dashboard"))

    # Get logged-in worker details
    user = get_user_by_username(session["username"])

    return render_template(
        "worker_dashboard.html",
        user=user
    )


# =========================
# MANAGER DASHBOARD
# =========================

@app.route("/manager-dashboard")
def manager_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only manager can access this page
    if session["role"] != "manager":
        return redirect(url_for("worker_dashboard"))

    conn = get_db_connection()

    # Get all workers and their latest detection
    workers = conn.execute("""
        SELECT
            u.id,
            u.name,
            u.username,
            u.worker_id,
            u.department,

            d.result AS latest_result,
            d.response_level AS latest_response,
            d.confidence AS latest_confidence,
            d.dominant_color AS latest_color,
            d.timestamp AS latest_time

        FROM users u

        LEFT JOIN detections d
        ON d.id = (
            SELECT d2.id
            FROM detections d2
            WHERE d2.user_id = u.id
            ORDER BY d2.id DESC
            LIMIT 1
        )

        WHERE u.role = 'worker'

        ORDER BY u.id
    """).fetchall()


    # Total workers
    total_workers = conn.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role = 'worker'
    """).fetchone()[0]


    # Total detections
    total_detections = conn.execute("""
        SELECT COUNT(*)
        FROM detections
    """).fetchone()[0]


    # Safe records
    safe_records = conn.execute("""
        SELECT COUNT(*)
        FROM detections
        WHERE result = 'SAFE'
    """).fetchone()[0]


    # Alerts
    alerts = conn.execute("""
        SELECT COUNT(*)
        FROM detections
        WHERE result IN ('WARNING', 'DANGER', 'VERY HIGH')
    """).fetchone()[0]


    conn.close()


    return render_template(
        "manager_dashboard.html",
        name=session["name"],
        workers=workers,
        total_workers=total_workers,
        total_detections=total_detections,
        safe_records=safe_records,
        alerts=alerts
    )


# =========================
# DETECTION PAGE
# =========================

@app.route("/detection")
def detection():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("detection.html")


# =========================
# SIMULATOR
# =========================

@app.route("/simulator")
def simulator():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("simulator.html")


# =========================
# HISTORY
# =========================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    # Worker sees only their own records
    if session["role"] == "worker":

        records = conn.execute("""
            SELECT
                detections.id,
                detections.timestamp,
                detections.mode,
                detections.result,
                detections.response_level,
                detections.confidence,
                detections.dominant_color

            FROM detections

            WHERE detections.user_id = ?

            ORDER BY detections.id DESC
        """, (session["user_id"],)).fetchall()


    # Manager sees all records
    else:

        records = conn.execute("""
            SELECT
                detections.id,
                detections.timestamp,
                detections.mode,
                detections.result,
                detections.response_level,
                detections.confidence,
                detections.dominant_color,
                users.name,
                users.worker_id

            FROM detections

            JOIN users
            ON detections.user_id = users.id

            ORDER BY detections.id DESC
        """).fetchall()


    conn.close()


    return render_template(
        "history.html",
        records=records,
        role=session["role"]
    )


# =========================
# ANALYZE IMAGE
# =========================

@app.route("/api/analyze", methods=["POST"])
def api_analyze():

    # -------------------------
    # CHECK LOGIN
    # -------------------------

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    # -------------------------
    # CHECK IMAGE
    # -------------------------

    if "image" not in request.files:

        return jsonify({
            "success": False,
            "message": "No image received."
        }), 400


    image_file = request.files["image"]


    if image_file.filename == "":

        return jsonify({
            "success": False,
            "message": "No image selected."
        }), 400


    try:

        # -------------------------
        # READ IMAGE
        # -------------------------

        image_bytes = image_file.read()


        # -------------------------
        # GET SELECTED CROP
        # -------------------------

        crop = None

        crop_data = request.form.get("crop")


        if crop_data:

            try:

                crop = json.loads(crop_data)

                print("Selected crop:", crop)

            except json.JSONDecodeError:

                print("Invalid crop data")

                crop = None


        # -------------------------
        # ANALYZE IMAGE
        # -------------------------

        result = analyze_strip(
            image_bytes,
            crop
        )


        # -------------------------
        # SAVE RESULT
        # -------------------------

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO detections
            (
                user_id,
                mode,
                result,
                response_level,
                confidence,
                dominant_color
            )

            VALUES (?, ?, ?, ?, ?, ?)
        """, (

            session["user_id"],

            "UPLOAD",

            result["result"],

            result["response_level"],

            result["confidence"],

            result["dominant_color"]

        ))


        conn.commit()

        conn.close()


        # -------------------------
        # SEND RESULT TO BROWSER
        # -------------------------

        return jsonify({

            "success": True,

            "result": result["result"],

            "visual_level": result["visual_level"],

            "ppm": result["ppm"],

            "ppm_range": result["ppm_range"],

            "status": result["status"],

            "status_message": result["status_message"],

            "response_level": result["response_level"],

            "confidence": result["confidence"],

            "dominant_color": result["dominant_color"]

        })


    except Exception as error:

        print(
            "Analysis error:",
            error
        )


        return jsonify({

            "success": False,

            "message": "Image analysis failed."

        }), 500


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    app.run(debug=True)