"""Flask application for the Digitization Process Management System."""

import csv
from io import StringIO
from datetime import datetime

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
import sqlite3
from functools import wraps
from database import (
    run_startup,
    add_user,
    authenticate_user,
    list_users,
    add_document,
    list_documents,
    get_document,
    add_process_tracking,
    update_document_details,
    list_document_updates,
    list_status_counts,
)

# Use pages/ as Jinja template folder to match current project structure.
app = Flask(__name__, template_folder="pages")
app.secret_key = "your-secret-key-change-in-production"

PROCESS_STATUSES = [
    "คัดเลือกเอกสาร",
    "สแกนเอกสาร",
    "ตรวจไฟล์ภาพสแกน",
    "ตกแต่งภาพสแกน",
    "สร้างและฝัง Metadata ใน PDF",
    "จัดเก็บ/สำรองไฟล์",
    "นำไฟล์เอกสารเข้าระบบคลังสารสนเทศดิจิทัล Metadata ใน PDF",
]

# Initialize database on startup
conn = run_startup()


def login_required(f):
    """Decorator to check if user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to allow access for admin users only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        if session.get("user_role") != "Admin":
            return "Forbidden", 403
        return f(*args, **kwargs)
    return decorated_function


# ==================== Authentication Routes ====================

@app.route("/", methods=["GET"])
def index():
    """Home page - redirect based on login status."""
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login page."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = authenticate_user(conn, email, password)
        if user:
            session["user_email"] = user["email"]
            session["user_name"] = user["user_name"]
            session["user_role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route("/logout", methods=["GET"])
def logout():
    """User logout."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Public registration is disabled. Accounts are created by admin only."""
    return "Registration is disabled. Please contact admin.", 403


# ==================== Dashboard Routes ====================

@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """Dashboard - show summary and recent documents."""
    status_counts = list_status_counts(conn)
    recent_docs = list_documents(conn)[:5]

    return render_template(
        "dashboard.html",
        status_counts=status_counts,
        recent_docs=recent_docs,
        user_name=session.get("user_name"),
    )


# ==================== Document Routes ====================

@app.route("/documents", methods=["GET"])
@login_required
def documents_list():
    """Display all documents."""
    docs = list_documents(conn)

    # Query controls for page-level search/filter/sort.
    query = request.args.get("q", "").strip().lower()
    status_filter = request.args.get("status", "").strip()
    sort_order = request.args.get("sort", "new")

    if query:
        docs = [
            d for d in docs
            if query in (d.get("title") or "").lower() or query in (d.get("file_name") or "").lower()
        ]

    if status_filter:
        docs = [d for d in docs if (d.get("current_status") or "") == status_filter]

    docs = sorted(
        docs,
        key=lambda d: ((d.get("last_completed_at") or d.get("created_at") or ""), d.get("file_name") or ""),
        reverse=(sort_order != "old"),
    )

    status_options = sorted({(d.get("current_status") or "") for d in list_documents(conn) if d.get("current_status")})

    return render_template(
        "documents_list.html",
        documents=docs,
        q=query,
        status_filter=status_filter,
        sort_order=sort_order,
        status_options=status_options,
    )


@app.route("/reports/download", methods=["GET"])
@login_required
def download_report():
    """Download document report as CSV."""
    docs = list_documents(conn)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["No", "FileName", "Title", "LatestStatus", "LastUpdatedAt"])

    for i, d in enumerate(docs, start=1):
        writer.writerow([
            i,
            d.get("file_name", ""),
            d.get("title", ""),
            d.get("current_status", ""),
            d.get("last_completed_at") or d.get("created_at") or "",
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=document_report.csv"
    return response


@app.route("/documents/add", methods=["GET", "POST"])
@admin_required
def add_document_page():
    """Add a new document."""
    if request.method == "POST":
        file_name = request.form.get("file_name", "").strip()
        user_name = request.form.get("user_name", "").strip()
        bib = request.form.get("bib", "").strip()
        call_number = request.form.get("call_number", "").strip()
        collection = request.form.get("collection", "").strip()
        title = request.form.get("title", "").strip()
        publish_date = request.form.get("publish_date", "")
        file_path = request.form.get("file_path", "").strip()

        publish_date = int(publish_date) if publish_date else None

        try:
            add_document(
                conn,
                file_name,
                user_name,
                bib,
                call_number,
                collection,
                title,
                publish_date,
                file_path,
            )
            return redirect(url_for("process_tracking_page", file_name=file_name, source="new"))
        except sqlite3.IntegrityError as e:
            error_msg = "Document with this file_name already exists"
            users = list_users(conn)
            return render_template("add_document.html", error=error_msg, users=users)

    users = list_users(conn)
    return render_template("add_document.html", users=users)


@app.route("/documents/<file_name>", methods=["GET"])
@login_required
def view_document(file_name):
    """View document details."""
    doc = get_document(conn, file_name)
    if not doc:
        return "Document not found", 404

    updates = list_document_updates(conn, file_name)

    q = request.args.get("q", "").strip().lower()
    status_filter = request.args.get("status", "").strip()
    sort_order = request.args.get("sort", "new")

    if q:
        updates = [
            u for u in updates
            if q in (u.get("status") or "").lower() or q in (u.get("user_name") or "").lower()
        ]

    if status_filter:
        updates = [u for u in updates if (u.get("status") or "") == status_filter]

    updates = sorted(
        updates,
        key=lambda u: ((u.get("completed_at") or u.get("created_at") or ""), u.get("transaction_id") or 0),
        reverse=(sort_order != "old"),
    )

    return render_template(
        "view_document.html",
        document=doc,
        updates=updates,
        process_statuses=PROCESS_STATUSES,
        q=q,
        status_filter=status_filter,
        sort_order=sort_order,
    )


@app.route("/documents/<file_name>/process-tracking", methods=["GET", "POST"])
@login_required
def process_tracking_page(file_name):
    """Display and update process tracking page for new/existing document workflows."""
    doc = get_document(conn, file_name)
    if not doc:
        return "Document not found", 404

    source = request.args.get("source", "update").strip().lower()
    is_new_case = source == "new"

    if is_new_case and session.get("user_role") != "Admin":
        return "Forbidden", 403

    if request.method == "POST":
        action = request.form.get("action", "").strip()

        if action == "edit_details" and session.get("user_role") == "Admin":
            publish_date_raw = request.form.get("publish_date", "").strip()
            publish_date = int(publish_date_raw) if (publish_date_raw and publish_date_raw.isdigit()) else None
            update_document_details(
                conn,
                file_name,
                request.form.get("user_name", "").strip() or doc.get("user_name", ""),
                request.form.get("bib", "").strip(),
                request.form.get("call_number", "").strip(),
                request.form.get("collection", "").strip(),
                request.form.get("title", "").strip(),
                publish_date,
                request.form.get("file_path", "").strip(),
            )

        if action == "update_status":
            selected_status = request.form.get("status", "").strip()
            completed_at = request.form.get("completed_at", "").strip() or None
            note = request.form.get("note", "").strip()

            if selected_status in PROCESS_STATUSES:
                if not completed_at:
                    completed_at = datetime.utcnow().replace(microsecond=0).isoformat()

                add_process_tracking(
                    conn,
                    file_name,
                    selected_status,
                    completed_at,
                    session.get("user_name"),
                    note,
                )

        return redirect(url_for("process_tracking_page", file_name=file_name, source="update"))

    updates = list_document_updates(conn, file_name)
    updates_asc = sorted(updates, key=lambda u: u.get("transaction_id") or 0)

    latest_status = None
    latest_by_status = {}
    for item in updates_asc:
        status_name = (item.get("status") or "").strip()
        if status_name in PROCESS_STATUSES:
            latest_status = status_name
            latest_by_status[status_name] = item

    current_idx = PROCESS_STATUSES.index(latest_status) if latest_status in PROCESS_STATUSES else -1
    latest_update = updates_asc[-1] if updates_asc else None

    timeline = []
    for idx, status_name in enumerate(PROCESS_STATUSES):
        if is_new_case:
            state = "new"
        elif current_idx >= 0 and idx < current_idx:
            state = "past"
        elif current_idx >= 0 and idx == current_idx:
            state = "current"
        else:
            state = "future"

        timeline.append(
            {
                "index": idx + 1,
                "status": status_name,
                "state": state,
                "is_top": idx % 2 == 0,
                "update": latest_by_status.get(status_name),
            }
        )

    breadcrumb = "เอกสารทั้งหมด > เพิ่มเอกสารใหม่"
    if not is_new_case:
        breadcrumb = f"เอกสารทั้งหมด > {doc.get('title') or '-'} > อัปเดตรายละเอียดข้อมูล/สถานะ"

    return render_template(
        "process_tracking.html",
        document=doc,
        breadcrumb=breadcrumb,
        is_new_case=is_new_case,
        timeline=timeline,
        latest_status=latest_status or PROCESS_STATUSES[0],
        latest_note=(latest_update.get("note") if latest_update else "") or "",
        process_statuses=PROCESS_STATUSES,
        can_edit_detail=session.get("user_role") == "Admin",
        users=list_users(conn) if session.get("user_role") == "Admin" else [],
    )


# ==================== Management Routes ====================

@app.route("/settings", methods=["GET"])
@login_required
def settings_page():
    """Display settings page for all users."""
    return render_template("setting.html")


@app.route("/system-management", methods=["GET"])
@admin_required
def system_management_page():
    """Display system management page for admins."""
    return render_template("system_management.html")


@app.route("/user-management", methods=["GET"])
@admin_required
def user_management_page():
    """Display user management page for admins."""
    users = list_users(conn)
    return render_template("user_management.html", users=users)


# ==================== API Routes ====================

@app.route("/api/users", methods=["GET"])
@login_required
def api_list_users():
    """API - List all users (JSON)."""
    users = list_users(conn)
    return jsonify([dict(u) for u in users])


@app.route("/api/documents", methods=["GET"])
@login_required
def api_list_documents():
    """API - List all documents (JSON)."""
    docs = list_documents(conn)
    return jsonify([dict(d) for d in docs])


@app.route("/api/documents/<file_name>", methods=["GET"])
@login_required
def api_get_document(file_name):
    """API - Get document by file_name (JSON)."""
    doc = get_document(conn, file_name)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    return jsonify(dict(doc))


@app.route("/api/documents/<file_name>/status", methods=["POST"])
@login_required
def api_update_status(file_name):
    """API - Update document status."""
    data = request.get_json()
    status = data.get("status", "").strip()
    completed_at = data.get("completed_at")

    try:
        add_process_tracking(conn, file_name, status, completed_at, session.get("user_name"))
        return jsonify({"success": True, "message": "Status updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/status-summary", methods=["GET"])
@login_required
def api_status_summary():
    """API - Get status summary (JSON)."""
    counts = list_status_counts(conn)
    return jsonify([dict(c) for c in counts])


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template("500.html"), 500


# ==================== Main ====================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)