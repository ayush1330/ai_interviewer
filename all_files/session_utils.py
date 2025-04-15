import streamlit as st

def reset_interview():
    """Reset the interview session state to start a new interview"""
    
    # Set a flag to show document selection options instead of immediately resetting
    if "show_document_options" not in st.session_state:
        st.session_state.show_document_options = True
        return
    
    # If the user chose to continue with existing documents
    if st.session_state.get("continue_with_existing", False):
        # Keep just the resume and cover letter paths
        temp_resume_path = st.session_state.get("resume_path", None)
        temp_cover_letter_path = st.session_state.get("cover_letter_path", None)
        job_description = st.session_state.get("job_description", "AI/ML position")
        
        # Clear all session state values
        for key in list(st.session_state.keys()):
            if key not in ["resume_path", "cover_letter_path"]:
                del st.session_state[key]
        
        # Restore just what we need
        if temp_resume_path:
            st.session_state.resume_path = temp_resume_path
        if temp_cover_letter_path:
            st.session_state.cover_letter_path = temp_cover_letter_path
        
        # Set job description
        st.session_state.job_description = job_description
        
        # Reset the flag
        st.session_state.continue_with_existing = False
    else:
        # If user wants to upload new documents or this is the default,
        # clear everything including document paths
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    # Force a rerun
    st.experimental_rerun()

def continue_with_existing_documents():
    """Continue with existing documents"""
    st.session_state.continue_with_existing = True
    st.session_state.show_document_options = False
    reset_interview()
    
def upload_new_documents():
    """Start fresh with new documents"""
    st.session_state.continue_with_existing = False
    st.session_state.show_document_options = False
    reset_interview() 