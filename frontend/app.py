
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ==================================================
# PROJECT CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

RECOMMENDATION_FILE = (
    BASE_DIR / "data" / "processed" / "job_recommendations.json"
)

CSS_FILE = BASE_DIR / "frontend" / "style.css"

# ==================================================
# DATABASE AND PROJECT MODULES
# ==================================================

from database.db import SessionLocal
from src.job_matching.job_model import Job

from src.tracking.application_tracking_service import (
    ALLOWED_TRANSITIONS,
    create_application,
    get_all_applications,
    get_application_history,
    get_application_statistics,
    update_application_status,
)

# ==================================================
# STREAMLIT CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="AI-JobPilot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================
# CUSTOM CSS
# ==================================================

def load_custom_css():
    if CSS_FILE.exists():
        css = CSS_FILE.read_text(encoding="utf-8")
        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )
    else:
        st.warning("Custom stylesheet not found: frontend/style.css")


load_custom_css()

# ==================================================
# DATA FUNCTIONS
# ==================================================

@st.cache_data
def load_recommendations():
    if not RECOMMENDATION_FILE.exists():
        return {}

    with RECOMMENDATION_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_database_job_count():
    with SessionLocal() as db:
        return db.query(Job).count()


def refresh_data():
    st.cache_data.clear()


def format_status(status):
    if not status:
        return "Initial"

    return str(status).replace("_", " ").title()


def format_timestamp(timestamp):
    if timestamp is None:
        return "Time unavailable"

    return timestamp.strftime("%d %b %Y · %I:%M %p")


def get_safe_score(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ==================================================
# LOAD DASHBOARD DATA
# ==================================================

recommendation_data = load_recommendations()
recommendations = recommendation_data.get("recommendations", [])
summary = recommendation_data.get("summary", {})

try:
    total_jobs = get_database_job_count()
    applications = get_all_applications()
    statistics = get_application_statistics()

except Exception as error:
    st.error(f"Unable to load dashboard data: {error}")
    st.stop()


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.title("🎯 AI-JobPilot")
    st.caption("INTELLIGENT JOB ASSISTANT")

    st.divider()

    page = st.radio(
        "MAIN MENU",
        [
            "Overview",
            "Job Recommendations",
            "Application Tracker",
        ],
        label_visibility="visible",
    )

    st.divider()

    st.markdown("### Candidate Profile")
    st.markdown("**JERIN RAY**")
    st.caption("B.Tech Artificial Intelligence & Data Science")
    st.caption("2026 Graduate")

    st.divider()

    if st.button(
        "🔄 Refresh Dashboard",
        use_container_width=True,
    ):
        refresh_data()
        st.rerun()

    st.caption("AI-JobPilot | Day 13")
    st.caption("Dashboard Version 3.1")


# ==================================================
# HEADER - FIXED HTML RENDERING
# ==================================================

# ==================================================
# HEADER - CLEAN VERSION
# ==================================================

st.title("🎯 AI-JobPilot Dashboard")

st.caption(
    "Discover opportunities. Analyze job matches. "
    "Manage your career journey."
)

st.divider()


st.divider()


# ==================================================
# PAGE 1: OVERVIEW AND LIVE ANALYTICS
# ==================================================

if page == "Overview":

    st.subheader("📊 Dashboard Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Jobs", total_jobs)

    with col2:
        st.metric(
            "Recommendations",
            summary.get("final_recommendations", 0),
        )

    with col3:
        st.metric("Applications", len(applications))

    with col4:
        st.metric(
            "India Opportunities",
            summary.get("india_or_india_remote_jobs", 0),
        )

    st.divider()

    # ------------------------------------------
    # APPLICATION STATUS SUMMARY
    # ------------------------------------------

    st.subheader("📈 Application Status")

    status_cards = [
        ("Prepared", "PREPARED"),
        ("Ready for Review", "READY_FOR_REVIEW"),
        ("Submitted", "SUBMITTED"),
        ("Failed", "FAILED"),
    ]

    cols = st.columns(4)

    for index, (label, status) in enumerate(status_cards):

        with cols[index]:
            st.metric(
                label,
                statistics.get(status, 0),
            )

    st.divider()

    # ------------------------------------------
    # JOB RECOMMENDATION ANALYSIS
    # ------------------------------------------

    st.subheader("🎯 Job Recommendation Analysis")

    india_count = summary.get(
        "india_or_india_remote_jobs", 0
    )

    fresher_count = summary.get(
        "potentially_fresher_friendly_jobs", 0
    )

    manual_count = summary.get(
        "manual_review_jobs", 0
    )

    if india_count == 0 or fresher_count == 0:

        st.warning(
            "Current recommendation data contains no confirmed "
            "India-based or potentially fresher-friendly opportunities. "
            "Verify each listing before applying."
        )

    analysis_col1, analysis_col2, analysis_col3 = st.columns(3)

    with analysis_col1:
        st.metric("India Opportunities", india_count)

    with analysis_col2:
        st.metric("Potential Fresher Roles", fresher_count)

    with analysis_col3:
        st.metric("Manual Review Required", manual_count)

    st.divider()

    # ------------------------------------------
    # ANALYTICS 1: APPLICATION STATUS DISTRIBUTION
    # ------------------------------------------

    st.subheader("📊 Application Status Distribution")

    status_data = {
        status: count
        for status, count in statistics.items()
        if status != "TOTAL" and count > 0
    }

    if status_data:

        status_df = pd.DataFrame({
            "Status": [
                status.replace("_", " ").title()
                for status in status_data
            ],
            "Applications": list(status_data.values()),
        }).set_index("Status")

        st.bar_chart(status_df)

    else:

        st.info(
            "Application status analytics will appear "
            "when applications are tracked."
        )

    st.divider()

    # ------------------------------------------
    # ANALYTICS 2: RECOMMENDATION SCORES
    # ------------------------------------------

    st.subheader("🎯 Job Recommendation Score Analysis")

    score_rows = []

    for job in recommendations:

        score = get_safe_score(
            job.get("suitability_score")
        )

        if score is None:
            continue

        score_rows.append({
            "Job": (
                f"{job.get('job_title', 'Unknown')} "
                f"- {job.get('company', 'Unknown')}"
            ),
            "Suitability Score": score,
        })

    if score_rows:

        score_df = pd.DataFrame(score_rows)

        score_df = score_df.sort_values(
            by="Suitability Score",
            ascending=False,
        )

        st.bar_chart(
            score_df.set_index("Job")
        )

        average_score = score_df[
            "Suitability Score"
        ].mean()

        st.metric(
            "Average Recommendation Score",
            f"{average_score:.1f}%",
        )

        st.caption(
            "Scores represent the recommendation engine output. "
            "They are not guarantees of interview selection."
        )

    else:

        st.info(
            "No recommendation scores are available."
        )

    st.divider()

    # ------------------------------------------
    # ANALYTICS 3: APPLICATION ACTIVITY
    # ------------------------------------------

    st.subheader("📅 Application Activity Timeline")

    activity_rows = []

    for app in applications:

        try:

            history_events = get_application_history(app.id)

            for event in history_events:

                if event.changed_at is not None:

                    activity_rows.append({
                        "Date": pd.Timestamp(
                            event.changed_at
                        ).date(),
                        "Event": event.event_type,
                        "Application ID": app.id,
                    })

        except Exception as error:

            st.warning(
                f"Could not load history for application "
                f"#{app.id}: {error}"
            )

    if activity_rows:

        activity_df = pd.DataFrame(activity_rows)

        daily_activity = (
            activity_df
            .groupby("Date")
            .size()
            .reset_index(name="Events")
            .set_index("Date")
            .sort_index()
        )

        st.line_chart(daily_activity)

        st.caption(
            f"Total recorded application events: "
            f"{len(activity_rows)}"
        )

    else:

        st.info(
            "Application activity will appear after "
            "application events are recorded."
        )

    st.divider()

    # ------------------------------------------
    # RECENT APPLICATIONS
    # ------------------------------------------

    st.subheader("📋 Recent Applications")

    if applications:

        recent_rows = [
            {
                "ID": app.id,
                "Company": app.company,
                "Role": app.job_title,
                "Status": app.status,
                "Created": format_timestamp(app.created_at),
            }
            for app in applications[:5]
        ]

        st.dataframe(
            pd.DataFrame(recent_rows),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No applications are currently being tracked."
        )


# ==================================================
# PAGE 2: JOB RECOMMENDATIONS
# ==================================================

elif page == "Job Recommendations":

    st.subheader("💼 Job Recommendations")

    if not recommendations:

        st.warning("No recommendation data available.")
        st.stop()

    st.caption(
        f"{len(recommendations)} ranked recommendations available."
    )

    search_col, location_col, eligibility_col = st.columns(3)

    with search_col:

        search_text = st.text_input(
            "🔍 Search jobs",
            placeholder="Search role or company...",
        )

    with location_col:

        locations = sorted({
            str(job.get("location") or "Unknown")
            for job in recommendations
        })

        selected_location = st.selectbox(
            "Location",
            ["All Locations"] + locations,
        )

    with eligibility_col:

        eligibility_options = sorted({
            str(job.get("fresher_eligibility") or "Unknown")
            for job in recommendations
        })

        selected_eligibility = st.selectbox(
            "Fresher Eligibility",
            ["All"] + eligibility_options,
        )

    filtered_jobs = []

    for job in recommendations:

        searchable = (
            str(job.get("job_title", ""))
            + " "
            + str(job.get("company", ""))
        ).lower()

        if search_text.lower() not in searchable:
            continue

        if (
            selected_location != "All Locations"
            and (job.get("location") or "Unknown")
            != selected_location
        ):
            continue

        if (
            selected_eligibility != "All"
            and job.get("fresher_eligibility")
            != selected_eligibility
        ):
            continue

        filtered_jobs.append(job)

    st.caption(
        f"Showing {len(filtered_jobs)} matching jobs."
    )

    if not filtered_jobs:

        st.info("No jobs match your selected filters.")

    for job in filtered_jobs:

        title = job.get("job_title") or "Unknown Role"
        company = job.get("company") or "Unknown Company"
        location = job.get("location") or "Unknown"

        with st.container(border=True):

            st.markdown(
                f"### #{job.get('rank', '-')} · {title}"
            )

            st.write(f"**{company}**")
            st.caption(f"📍 {location}")

            score_col, skill_col, eligibility_col = st.columns(3)

            with score_col:

                score = job.get("suitability_score")

                st.metric(
                    "Suitability Score",
                    f"{score}%" if score is not None else "N/A",
                )

            with skill_col:

                match = job.get(
                    "mandatory_skill_match_percentage"
                )

                st.metric(
                    "Skill Match",
                    f"{match}%" if match is not None else "N/A",
                )

            with eligibility_col:

                eligibility = (
                    job.get("fresher_eligibility") or "Unknown"
                )

                st.write("**Fresher Eligibility**")

                st.write(
                    eligibility.replace("_", " ").title()
                )

            if job.get("manual_verification_required", True):

                st.warning(
                    "Manual verification required before applying."
                )

            matched = (
                job.get("matched_mandatory_skills") or []
            )

            missing = (
                job.get("missing_mandatory_skills") or []
            )

            st.write(
                "**Matched Skills:** "
                + (
                    ", ".join(matched)
                    if matched
                    else "Not available"
                )
            )

            st.write(
                "**Missing Skills:** "
                + (
                    ", ".join(missing)
                    if missing
                    else "None listed"
                )
            )

            with st.expander("View recommendation details"):

                for reason in (
                    job.get("recommendation_reasons") or []
                ):

                    st.write(f"• {reason}")

                st.write(
                    f"Source: {job.get('source', 'Unknown')}"
                )

                st.write(
                    f"Job ID: {job.get('job_id')}"
                )

            apply_url = job.get("apply_url")

            if apply_url:

                st.markdown(
                    f"[Open Original Job Listing]({apply_url})"
                )

            if st.button(
                "＋ Add to Application Tracker",
                key=f"track_{job.get('job_id')}",
            ):

                try:

                    application, created = create_application(
                        job_id=int(job["job_id"]),
                        candidate_name="JERIN RAY",
                        status="PREPARED",
                    )

                    if created:

                        st.success(
                            f"Application #{application.id} "
                            "added successfully."
                        )

                    else:

                        st.info(
                            "This job is already in your tracker."
                        )

                    st.rerun()

                except Exception as error:

                    st.error(
                        f"Unable to add this job: {error}"
                    )


# ==================================================
# PAGE 3: APPLICATION TRACKER
# ==================================================

elif page == "Application Tracker":

    st.subheader("📁 Application Tracker")

    st.caption(
        "Monitor application preparation, review, submission "
        "and subsequent progress."
    )

    stat_cols = st.columns(4)

    tracker_statuses = [
        ("Prepared", "PREPARED"),
        ("Ready for Review", "READY_FOR_REVIEW"),
        ("Submitted", "SUBMITTED"),
        ("Failed", "FAILED"),
    ]

    for index, (label, status) in enumerate(tracker_statuses):

        with stat_cols[index]:

            st.metric(
                label,
                statistics.get(status, 0),
            )

    st.divider()

    # ------------------------------------------
    # ALL APPLICATIONS
    # ------------------------------------------

    st.subheader("All Applications")

    if not applications:

        st.info("No tracked applications found.")

    else:

        application_rows = []

        for app in applications:

            application_rows.append({
                "Application ID": app.id,
                "Job ID": app.job_id,
                "Company": app.company,
                "Job Title": app.job_title,
                "Status": app.status,
                "Retry Count": app.retry_count,
                "Created At": format_timestamp(app.created_at),
                "Last Error": app.last_error or "-",
            })

        st.dataframe(
            pd.DataFrame(application_rows),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # ------------------------------------------
        # APPLICATION DETAILS
        # ------------------------------------------

        st.subheader("🔎 Application Details")

        application_options = {
            (
                f"#{app.id} · "
                f"{app.company} · "
                f"{app.job_title}"
            ): app.id
            for app in applications
        }

        selected_label = st.selectbox(
            "Select Application",
            list(application_options.keys()),
            key="selected_application",
        )

        selected_id = application_options[selected_label]

        selected_app = next(
            app
            for app in applications
            if app.id == selected_id
        )

        st.write(
            f"**Company:** {selected_app.company}"
        )

        st.write(
            f"**Role:** {selected_app.job_title}"
        )

        st.write(
            f"**Current Status:** "
            f"{format_status(selected_app.status)}"
        )

        if selected_app.application_url:

            st.markdown(
                f"[Open Application Website]"
                f"({selected_app.application_url})"
            )

        st.divider()

        # ------------------------------------------
        # UPDATE APPLICATION STATUS
        # ------------------------------------------

        st.subheader("✏️ Update Application Status")

        allowed_statuses = sorted(
            ALLOWED_TRANSITIONS.get(
                selected_app.status,
                set(),
            )
        )

        if allowed_statuses:

            with st.form("application_status_form"):

                new_status = st.selectbox(
                    "New Status",
                    allowed_statuses,
                )

                details = st.text_area(
                    "Notes / Update Details",
                    placeholder=(
                        "Enter application update details..."
                    ),
                )

                update_button = st.form_submit_button(
                    "Update Application"
                )

                if update_button:

                    try:

                        update_application_status(
                            application_id=selected_id,
                            new_status=new_status,
                            details=details.strip() or None,
                        )

                        st.success(
                            "Application status updated successfully."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Status update failed: {error}"
                        )

        else:

            st.info(
                "No further status transitions are available."
            )

        st.divider()

        # ------------------------------------------
        # APPLICATION HISTORY TIMELINE
        # ------------------------------------------

        st.subheader("🕒 Application History Timeline")

        st.caption(
            "A chronological record of events and status changes "
            "for this application."
        )

        try:

            history = get_application_history(selected_id)

            if not history:

                st.info(
                    "No history events are available "
                    "for this application."
                )

            else:

                st.markdown(
                    f"**{len(history)} history event(s) recorded.**"
                )

                for index, event in enumerate(history):

                    with st.container(border=True):

                        event_col, details_col = st.columns([1, 5])

                        with event_col:

                            if index == 0:
                                st.markdown("### 🟢")
                            else:
                                st.markdown("### 🔵")

                            st.caption(
                                f"Event {index + 1}"
                            )

                        with details_col:

                            event_name = format_status(
                                event.event_type
                            )

                            st.markdown(
                                f"**{event_name}**"
                            )

                            old_status = format_status(
                                event.old_status
                            )

                            new_status = format_status(
                                event.new_status
                            )

                            if (
                                event.old_status
                                or event.new_status
                            ):

                                st.write(
                                    f"**Status:** "
                                    f"{old_status} → {new_status}"
                                )

                            st.caption(
                                format_timestamp(event.changed_at)
                            )

                            if event.details:

                                st.write(event.details)

        except Exception as error:

            st.error(
                f"Unable to load application history: {error}"
            )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align: center;
        color: #718096;
        padding: 15px;
        font-size: 12px;
    ">
        <strong>AI-JobPilot</strong> · Intelligent Career Management
        <br>
        Dashboard Version 3.1 · Day 13
        <br>
        Applications require human review and authorization.
    </div>
    """,
    unsafe_allow_html=True,
)
