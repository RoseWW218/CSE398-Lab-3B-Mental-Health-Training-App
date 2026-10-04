import streamlit as st
from llm import patient_reply, session_feedback, session_summary
from auth import require_login
from patients import (
    PRESET_PATIENTS,
    create_patient,
    get_patient,
    list_patients,
)
from sessions import (
    save_session,
    update_session_feedback,
    list_sessions,
    get_session,
    update_session_summary,
)

st.set_page_config(
    page_title="Counseling Training App",
    page_icon="💬",
    layout="wide",
)

st.title("Counseling Training App")
st.write(
    "Practice counseling skills through conversations "
    "with simulated patients."
)
st.caption("For educational practice only. All patient profiles are fictional.")

username = require_login()

if "page" not in st.session_state:
    st.session_state.page = "home"


def show_profile(patient):
    st.subheader(patient["name"])

    col1, col2, col3 = st.columns(3)
    col1.write(f"**Gender:** {patient['gender']}")
    col2.write(f"**Age group:** {patient['age_group']}")
    col3.write(f"**Ethnicity:** {patient['ethnicity']}")

    st.write("**Main concern:**", patient["concern"])
    st.write("**Background:**", patient["background"])
    st.write("**Communication style:**", patient["communication_style"])
    st.write("**Key symptoms:**", patient["key_symptoms"])


if st.session_state.page == "home":
    st.subheader(f"Welcome, {username}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Real Patients", use_container_width=True):
            st.info("The real-patient section is not configured yet.")

    with col2:
        if st.button("Simulated Patients", use_container_width=True):
            st.session_state.page = "patients"
            st.rerun()


elif st.session_state.page == "patients":
    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.header("Simulated Patients")

    notice = st.session_state.pop("patient_notice", None)
    if notice:
        st.success(notice)

    preset_tab, custom_tab, existing_tab = st.tabs(
        ["Preset Patients", "Create a Patient", "Saved Patients"]
    )

    with preset_tab:
        st.write("Choose a fictional patient adapted from the assignment examples.")

        selected_preset = st.selectbox(
            "Patient persona",
            list(PRESET_PATIENTS),
        )

        profile = PRESET_PATIENTS[selected_preset]
        show_profile(profile)

        if st.button("Save This Patient", key="save_preset"):
            create_patient(username=username, **profile)
            st.session_state.patient_notice = (
                f"{profile['name']} saved. Open the Saved Patients tab "
                "to select this patient."
            )
            st.rerun()

    with custom_tab:
        st.write("Create your own fictional patient.")

        with st.form("create_patient_form"):
            name = st.text_input("Fictional name")

            col1, col2 = st.columns(2)

            with col1:
                gender = st.selectbox(
                    "Gender",
                    ["Female", "Male", "Non-binary", "Not specified"],
                )
                age_group = st.selectbox(
                    "Age group",
                    ["18–25", "26–35", "36–45", "46–60", "61+"],
                )

            with col2:
                ethnicity = st.text_input(
                    "Ethnicity",
                    value="Not specified",
                )
                concerns = st.multiselect(
                    "Mental health concerns",
                    [
                        "Academic stress",
                        "Parent-child relationship",
                        "Cultural adjustment",
                        "Anxiety",
                        "Low mood",
                        "Work-related burnout",
                        "Social isolation",
                        "Other",
                    ],
                )

            background = st.text_area(
                "Background",
                placeholder="Describe the fictional patient's situation.",
            )
            communication_style = st.text_area(
                "Communication style",
                placeholder="For example: quiet and hesitant to open up.",
            )
            key_symptoms = st.text_area(
                "Key symptoms",
                placeholder="For example: poor sleep and difficulty concentrating.",
            )

            submitted = st.form_submit_button("Save Patient")

        if submitted:
            if not name.strip():
                st.error("Please enter a fictional name.")
            elif not concerns:
                st.error("Please select at least one concern.")
            elif not all(
                text.strip()
                for text in (background, communication_style, key_symptoms)
            ):
                st.error(
                    "Please complete the background, communication style, "
                    "and key symptoms."
                )
            else:
                create_patient(
                    username=username,
                    name=name.strip(),
                    gender=gender,
                    age_group=age_group,
                    ethnicity=ethnicity.strip() or "Not specified",
                    concern=", ".join(concerns),
                    background=background.strip(),
                    communication_style=communication_style.strip(),
                    key_symptoms=key_symptoms.strip(),
                )
                st.session_state.patient_notice = (
                    f"{name.strip()} saved. Open the Saved Patients tab "
                    "to select this patient."
                )
                st.rerun()

    with existing_tab:
        saved_patients = list_patients(username)

        if not saved_patients:
            st.info("No saved patients yet. Save a preset or create a patient first.")
        else:
            patient_lookup = {
                patient["id"]: patient
                for patient in saved_patients
            }

            selected_id = st.selectbox(
                "Choose a saved patient",
                list(patient_lookup),
                format_func=lambda patient_id: (
                    f"{patient_lookup[patient_id]['name']} — "
                    f"{patient_lookup[patient_id]['concern']} "
                    f"(#{patient_id})"
                ),
            )

            patient = get_patient(username, selected_id)

            if patient:
                show_profile(patient)
                previous_sessions = list_sessions(username, patient["id"])

                with st.expander("Previous Sessions"):
                    if not previous_sessions:
                        st.info("No saved sessions yet.")
                    else:
                        for record in previous_sessions:
                            with st.expander(
                                f"Session #{record['id']} — "
                                f"{record['created_at']} (UTC)"
                            ):

                                saved = get_session(username, record["id"])

                                if saved:
                                    record_tab, summary_tab, feedback_tab = st.tabs(
                                        ["Conversation Record", "Summary", "Feedback"]
                                    )

                                    with record_tab:
                                        for message in saved["messages"]:
                                            role = (
                                                "Counselor"
                                                if message["role"] == "user"
                                                else "Patient"
                                            )
                                            st.markdown(
                                                f"**{role}:** {message['content']}"
                                            )

                                    with summary_tab:
                                        if saved["summary"]:
                                            st.markdown("**Session Summary**")
                                            st.markdown(saved["summary"])
                                        else:
                                            if st.button(
                                                "Generate Summary for This Session",
                                                key=f"saved_summary_{saved['id']}",
                                            ):
                                                try:
                                                    with st.spinner("Preparing your session summary..."):
                                                        summary = session_summary(
                                                            patient,
                                                            saved["messages"],
                                                        )
                                                    update_session_summary(
                                                        username=username,
                                                        session_id=saved["id"],
                                                        summary=summary,
                                                    )
                                                except Exception as exc:
                                                    error_code = getattr(exc, "code", None)

                                                    if str(error_code) == "429":
                                                        st.error(
                                                            "The model's API quota or rate limit has been reached. "
                                                            "Please try again later. "
                                                            "Your saved conversation is still available."
                                                        )
                                                    elif str(error_code) == "503":
                                                        st.error(
                                                            "The model is temporarily unavailable. "
                                                            "Please try again later."
                                                        )
                                                    else:
                                                        st.error(
                                                            f"Summary failed: {type(exc).__name__}. "
                                                            "Please check the terminal for details."
                                                        )

                                                    print(
                                                        "Session summary failed:",
                                                        type(exc).__name__,
                                                        str(exc),
                                                    )
                                                else:
                                                    st.rerun()

                                    with feedback_tab:
                                        if saved["feedback"]:
                                            st.markdown("**Saved Feedback**")
                                            st.markdown(saved["feedback"])
                                        elif any(
                                            message["role"] == "user"
                                            for message in saved["messages"]
                                        ):
                                            if st.button(
                                                "Generate Feedback for This Session",
                                                key=f"saved_feedback_{saved['id']}",
                                            ):
                                                try:
                                                    with st.spinner("Preparing your feedback report..."):
                                                        feedback = session_feedback(
                                                            patient,
                                                            saved["messages"],
                                                        )
                                                    update_session_feedback(
                                                        username=username,
                                                        session_id=saved["id"],
                                                        feedback=feedback,
                                                    )
                                                except Exception as exc:
                                                    error_code = getattr(exc, "code", None)

                                                    if str(error_code) == "429":
                                                        st.error(
                                                            "The model's API quota or rate limit has been reached. "
                                                            "Please try again later. "
                                                            "Your saved conversation is still available."
                                                        )
                                                    elif str(error_code) == "503":
                                                        st.error(
                                                            "The model is temporarily unavailable. "
                                                            "Please try again later."
                                                        )
                                                    else:
                                                        st.error(
                                                            f"Feedback failed: {type(exc).__name__}. "
                                                            "Please check the terminal for details."
                                                        )

                                                    print(
                                                        "Saved session feedback failed:",
                                                        type(exc).__name__,
                                                        str(exc),
                                                    )
                                                else:
                                                    st.rerun()

                                st.divider()
                if st.button("Start Session", key="start_session"):
                    st.session_state.active_patient_id = patient["id"]
                    st.session_state.messages = []
                    st.session_state.saved_session_id = None
                    st.session_state.feedback = None
                    st.session_state.session_ended = False
                    st.session_state.page = "chat"
                    st.rerun()
elif st.session_state.page == "chat":
    patient = get_patient(
        username,
        st.session_state.get("active_patient_id"),
    )

    if not patient:
        st.error("Patient not found.")
        if st.button("Return to Patients"):
            st.session_state.page = "patients"
            st.rerun()
        st.stop()

    st.header(f"Counseling Session — {patient['name']}")
    previous_sessions = list_sessions(username, patient["id"])
    if previous_sessions:
        latest_session = previous_sessions[0]
        with st.expander("Previous Session Summary", expanded=True):
            if latest_session["summary"]:
                st.markdown(latest_session["summary"])
            else:
                st.info(
                    "The latest saved session does not have a summary yet. "
                    "You can generate one under Previous Sessions."
                )

    with st.expander("Patient Profile"):
        show_profile(patient)

    st.caption("You are the counselor. The AI plays the fictional patient.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_ended" not in st.session_state:
        st.session_state.session_ended = False

    # Generate the patient's opening only when the conversation is empty.
    if not st.session_state.messages:
        try:
            with st.spinner("The patient is preparing their opening message..."):
                opening = patient_reply(patient, [])

            st.session_state.messages = [
                {"role": "assistant", "content": opening}
            ]
            st.rerun()

        except Exception:
            st.error(
                "Could not generate the patient's opening. "
                "Check your connection and API availability, then try again."
            )

            if st.button("Retry Opening"):
                st.rerun()

            if st.button("Back to Patients", key="opening_back"):
                st.session_state.page = "patients"
                st.rerun()

            st.stop()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.session_ended:
        if st.button("End Session"):
            try:
                session_id = save_session(
                    username=username,
                    patient_id=patient["id"],
                    messages=st.session_state.messages,
                )
            except Exception as exc:
                st.error("Could not save the session. Please try again.")
                print("Session save failed:", type(exc).__name__, str(exc))
            else:
                st.session_state.saved_session_id = session_id
                st.session_state.session_ended = True
                st.rerun()

        counselor_message = st.chat_input(
            "Respond as the counselor..."
        )

        if counselor_message and counselor_message.strip():
            new_message = {
                "role": "user",
                "content": counselor_message.strip(),
            }

            # Commit the new exchange only after a successful API response.
            pending_messages = (
                st.session_state.messages + [new_message]
            )

            try:
                with st.spinner("The patient is responding..."):
                    reply = patient_reply(patient, pending_messages)

                st.session_state.messages = pending_messages + [
                    {"role": "assistant", "content": reply}
                ]
                st.rerun()

            except Exception as exc:
                st.error(
                    f"Patient reply failed: {type(exc).__name__}"
                )
                print(
                    "Patient reply failed:",
                    type(exc).__name__,
                    str(exc),
                )
                st.info(
                    "Your unsent message: "
                    + counselor_message.strip()
                )

    else:
        st.success("Session ended.")

        has_counselor_message = any(
            message["role"] == "user"
            for message in st.session_state.messages
        )

        if not has_counselor_message:
            st.info(
                "No counselor responses were recorded, "
                "so this session cannot be evaluated."
            )

        elif not st.session_state.get("feedback"):
            if st.button("Feedback on the Counselling Session"):
                try:
                    with st.spinner("Preparing your feedback report..."):
                        feedback = session_feedback(
                            patient,
                            st.session_state.messages,
                        )

                    session_id = st.session_state.get("saved_session_id")

                    if session_id is None:
                        session_id = save_session(
                            username=username,
                            patient_id=patient["id"],
                            messages=st.session_state.messages,
                        )
                        st.session_state.saved_session_id = session_id

                    update_session_feedback(
                        username=username,
                        session_id=session_id,
                        feedback=feedback,
                    )

                    st.session_state.feedback = feedback
                    st.rerun()

                except Exception as exc:
                    error_code = getattr(exc, "code", None)

                    if str(error_code) == "429":
                        st.error(
                            "The model's API quota or rate limit has been reached. "
                            "Please try again later. "
                            "You can retry feedback from Previous Sessions."
                        )
                    elif str(error_code) == "503":
                        st.error(
                            "The model is temporarily unavailable. "
                            "Please try again later."
                        )
                    else:
                        st.error(
                            f"Feedback failed: {type(exc).__name__}. "
                            "Please check the terminal for details."
                        )
                    print(
                        "Feedback generation failed:",
                        type(exc).__name__,
                        str(exc),
                    )

        if st.session_state.get("feedback"):
            st.subheader("Counseling Feedback")
            st.markdown(st.session_state.feedback)

            st.download_button(
                "Download Feedback",
                data=st.session_state.feedback,
                file_name="counseling_feedback.md",
                mime="text/markdown",
            )

        st.caption("Your conversation has been saved. You can view it under Previous Sessions.")

        if st.button("Back to Patients", key="ended_back"):
            st.session_state.page = "patients"
            st.rerun()