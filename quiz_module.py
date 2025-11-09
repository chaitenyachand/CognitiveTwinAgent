
# quiz_module.py
import streamlit as st
import generative_ai
import database_utils as db

def setup_quiz(topic_text, topic_id, num_questions=5):
    """Generates and stores a quiz in the session state."""
    quiz_data = generative_ai.generate_quiz(topic_text, num_questions=num_questions)
    if quiz_data and "quiz" in quiz_data:
        st.session_state.current_quiz = quiz_data["quiz"]
        st.session_state.current_topic_id = topic_id
        st.session_state.user_answers = [None] * len(quiz_data["quiz"])
    else:
        st.error("Failed to generate quiz. Please try again.")

def display_quiz():
    """Displays the quiz questions and widgets. Returns True if submitted."""
    if "current_quiz" not in st.session_state:
        st.warning("No quiz loaded.")
        return False

    for i, q in enumerate(st.session_state.current_quiz):
        st.subheader(f"Question {i+1}: {q['question']}")
        st.caption(f"Topic: {q['topic']}")
        
        q_type = q.get("type", "MCQ")
        
        if q_type == "MCQ":
            # Extract just the option text without the letter prefix
            options = [opt.split(".", 1)[-1].strip() if "." in opt else opt for opt in q['options']]
            st.session_state.user_answers[i] = st.radio(
                "Your answer:", 
                options, 
                key=f"q_{i}",
                index=None
            )
        
        elif q_type == "T/F":
            st.session_state.user_answers[i] = st.radio(
                "Your answer:", 
                q['options'], 
                key=f"q_{i}",
                index=None
            )
        
        elif q_type == "Short":
            st.session_state.user_answers[i] = st.text_input(
                "Your answer:", 
                key=f"q_{i}"
            )

    st.divider()
    if st.button("Submit Quiz", type="primary"):
        if None in st.session_state.user_answers or "" in st.session_state.user_answers:
            st.warning("Please answer all questions before submitting.")
            return False
        return True
    return False

def grade_and_store_quiz():
    """Grades the quiz and stores results."""
    
    quiz_data = st.session_state.get("current_quiz", None)
    user_answers = st.session_state.get("user_answers", [])
    
    if not quiz_data or not isinstance(quiz_data, list):
        st.error("Quiz data is missing or invalid. Cannot grade quiz. Please go back and try again.")
        st.session_state.latest_score = 0
        st.session_state.latest_weak_areas = []
        return

    correct_count = 0
    weak_areas = []
    
    try:
        st.subheader("Quiz Results")
        
        for i, q in enumerate(quiz_data):
            q_type = q.get("type", "MCQ")
            user_answer = user_answers[i] if i < len(user_answers) else None
            is_correct = False
            
            # Different grading logic based on question type
            if q_type == "MCQ":
                # Extract the correct letter from the answer
                correct_letter = q['answer'].strip().upper()
                
                # Get user's answer and extract letter
                if user_answer:
                    # Find which option matches the user's answer
                    for opt in q['options']:
                        opt_text = opt.split(".", 1)[-1].strip() if "." in opt else opt
                        if opt_text == user_answer:
                            user_letter = opt.split(".")[0].strip().upper()
                            is_correct = (user_letter == correct_letter)
                            break
            
            elif q_type == "T/F":
                correct_answer = q['answer'].strip()
                is_correct = (user_answer == correct_answer)
            
            elif q_type == "Short":
                # Check if any of the keywords are in the user's answer
                keywords = q.get('answer_keywords', [])
                if user_answer and keywords:
                    user_answer_lower = user_answer.lower()
                    is_correct = any(keyword.lower() in user_answer_lower for keyword in keywords)
            
            # Display result
            with st.container(border=True):
                st.markdown(f"**Question {i+1}:** {q['question']}")
                
                if is_correct:
                    correct_count += 1
                    st.success(f"✅ Correct! Your answer: {user_answer}")
                else:
                    weak_areas.append(q.get('topic', 'General'))
                    st.error(f"❌ Incorrect. Your answer: {user_answer}")
                    
                    # Show correct answer
                    if q_type == "MCQ":
                        correct_opt = [opt for opt in q['options'] if opt.startswith(q['answer'])][0]
                        st.info(f"Correct answer: {correct_opt}")
                    elif q_type == "T/F":
                        st.info(f"Correct answer: {q['answer']}")
                    elif q_type == "Short":
                        st.info(f"Expected keywords: {', '.join(q.get('answer_keywords', []))}")
        
        # Calculate score
        total_questions = len(quiz_data)
        final_score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        st.divider()
        st.metric(label="Your Score", value=f"{final_score:.1f}%")
        st.write(f"You answered {correct_count} out of {total_questions} questions correctly.")

        # Save results to session state
        st.session_state.latest_score = final_score
        st.session_state.latest_weak_areas = list(set(weak_areas))
        
        # Save to database
        db.save_quiz_result(
            st.session_state.user_id,
            st.session_state.current_topic_id,
            final_score,
            total_questions,
            st.session_state.latest_weak_areas
        )
        
    except Exception as e:
        st.error(f"An error occurred while grading the quiz: {e}")
        print(f"Grading error: {e}")
        st.session_state.latest_score = 0
        st.session_state.latest_weak_areas = []