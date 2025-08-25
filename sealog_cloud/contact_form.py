import streamlit as st
from datetime import datetime
import json
import os

# Import the centralized email service
from services.email_service import send_feedback_email

def render_contact_form():
    """Render the contact form - Updated to use centralized email service"""
    
    st.title(" Feature Request / Bug Report")
    st.markdown("*Help us improve The SeaLog Cloud by sharing your feedback*")
    st.markdown("---")
    
    # Create two columns for the form
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("contact_form", clear_on_submit=True):
            st.subheader(" Tell us about it")
            
            # Contact type selection
            contact_type = st.selectbox(
                "What type of feedback is this?",
                [" Bug Report", " Feature Request", " General Question", " Other Feedback"]
            )
            
            # Subject line
            subject = st.text_input(
                "Subject",
                placeholder="Brief description of your request or issue"
            )
            
            # Priority level
            priority = st.selectbox(
                "Priority Level",
                [" High - Critical issue affecting functionality", 
                 " Medium - Important but not critical", 
                 " Low - Nice to have improvement"]
            )
            
            # Detailed description
            description = st.text_area(
                "Detailed Description",
                placeholder="Please provide as much detail as possible...",
                height=200,
                help="For bug reports: include steps to reproduce, expected vs actual behavior\nFor feature requests: describe the problem you're trying to solve"
            )
            
            # Additional context
            st.subheader(" Additional Information")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                affected_tool = st.selectbox(
                    "Which tool does this relate to?",
                    ["General App", "Crew Logbook", "Ships Logbook", "Hours of Rest", 
                     "Watch Scheduler", "Fuel Burn Calculator", "Conversion Tools", 
                     "Risk Assessment", "Country Log", "Profile", "Settings", "Other"]
                )
            
            with col_b:
                browser_info = st.text_input(
                    "Browser/Device (optional)",
                    placeholder="e.g., Chrome on Windows, Safari on iPhone"
                )
            
            # Contact preference
            contact_method = st.radio(
                "How would you like us to follow up?",
                [" Email me when this is addressed", " No follow-up needed"]
            )
            
            # Submit button
            submitted = st.form_submit_button(
                " Submit Feedback", 
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not subject.strip():
                    st.error("Please provide a subject for your feedback.")
                elif not description.strip():
                    st.error("Please provide a detailed description.")
                else:
                    # Process the form submission using centralized service
                    form_data = {
                        'type': contact_type,
                        'subject': subject,
                        'priority': priority,
                        'description': description,
                        'affected_tool': affected_tool,
                        'browser_info': browser_info,
                        'contact_method': contact_method,
                        'username': getattr(st.session_state, 'username', 'Anonymous'),
                        'user_id': getattr(st.session_state, 'user_id', 'Unknown'),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # THIS IS THE ONLY CHANGE - using centralized service
                    success = handle_form_submission_centralized(form_data)
                    
                    if success:
                        st.success(" Thank you! Your feedback has been submitted successfully.")
                        st.balloons()
                    else:
                        st.error(" There was an issue submitting your feedback. Please try again or contact us directly.")
    
    with col2:
        # Information sidebar (unchanged)
        st.subheader("ℹ Getting Help")
        
        st.info("""
        **Quick Tips:**
        
         **Bug Reports:**
        - Describe what you expected vs what happened
        - Include steps to reproduce
        - Mention any error messages
        
         **Feature Requests:**
        - Explain the problem you're trying to solve
        - Describe your ideal solution
        - Mention how it would help your workflow
        """)
        
        st.markdown("---")
        
        st.subheader(" Direct Contact")
        st.markdown("""
        **Email:** support@sealogcloud.com
        
        **Response Time:**
        -  Critical: 24 hours
        -  Medium: 2-3 days  
        -  Low: 1 week
        """)
        
        st.markdown("---")
        
        # FAQ section
        with st.expander(" Frequently Asked Questions"):
            st.markdown("""
            **Q: How long until my feature is implemented?**
            A: Feature requests are prioritized based on user demand and development complexity. We'll keep you updated!
            
            **Q: Can I suggest improvements to existing tools?**
            A: Absolutely! We love suggestions for improving current functionality.
            
            **Q: Is my data safe when reporting bugs?**
            A: Yes, we never ask for or store personal logbook data in bug reports.
            """)


def handle_form_submission_centralized(form_data):
    """Handle form submission using the centralized email service"""
    
    try:
        # Save to local file as backup (same as before)
        save_feedback_to_file(form_data)
        
        # Send via centralized email service - THIS IS THE MAIN CHANGE
        email_sent = send_feedback_email(form_data)
        
        if email_sent:
            return True
        else:
            # Even if email fails, we saved locally
            st.warning(" Feedback saved locally. Email delivery may be delayed.")
            return True
        
    except Exception as e:
        st.error(f"Error processing feedback: {str(e)}")
        return False


def save_feedback_to_file(form_data):
    """Save feedback to a local JSON file as backup (unchanged)"""
    
    try:
        # Create feedback directory if it doesn't exist
        feedback_dir = "feedback"
        if not os.path.exists(feedback_dir):
            os.makedirs(feedback_dir)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feedback_{timestamp}.json"
        filepath = os.path.join(feedback_dir, filename)
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(form_data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        st.error(f"Error saving feedback to file: {str(e)}")
        return False


# Optional: Test function for the centralized service
def test_centralized_email_service():
    """Test the centralized email service from the contact form"""
    
    st.subheader(" Test Centralized Email Service")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Test Feedback Email"):
            test_form_data = {
                'type': ' Test',
                'subject': 'Test Email from Contact Form',
                'priority': ' Medium - Important but not critical',
                'description': 'This is a test email to verify the centralized email service is working with the contact form.',
                'affected_tool': 'Contact Form',
                'browser_info': 'Test Browser',
                'contact_method': ' No follow-up needed',
                'username': getattr(st.session_state, 'username', 'Test User'),
                'user_id': getattr(st.session_state, 'user_id', 'test_123'),
                'timestamp': datetime.now().isoformat()
            }
            
            success = send_feedback_email(test_form_data)
            
            if success:
                st.success(" Test email sent successfully!")
            else:
                st.error(" Test email failed to send")
    
    with col2:
        test_email = st.text_input("Test Email Address", placeholder="your-email@example.com")
        
        if st.button("Test Direct Email") and test_email:
            from services.email_service import test_email_service
            
            success = test_email_service(test_email)
            
            if success:
                st.success(f" Test email sent to {test_email}!")
            else:
                st.error(" Test email failed to send")


# Uncomment this line to show the test functions
# test_centralized_email_service()