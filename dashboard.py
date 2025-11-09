# dashboard.py
import streamlit as st
import os
import sys # <-- IMPORTED SYS

# --- Robust Import Logic ---
# Add the project's root directory (where app.py is) to the Python path
# This ensures that all module imports (utils, auth, etc.) work reliably
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import database_utils as db
import generative_ai
import plotly.graph_objects as go
from utils import render_markmap_html, render_flashcards
import json
import pandas as pd
import time
from datetime import datetime, timedelta
import calendar
# --- Global CSS Fixes ---
st.markdown("""
    <style>
        /* Prevent content overlap */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Add margin below each section */
        .section {
            margin-bottom: 2.5rem;
        }

        /* Prevent text overlap */
        .stMarkdown p {
            line-height: 1.6;
            word-wrap: break-word;
        }

        /* Fix for columns overlapping when resizing */
        [data-testid="column"] {
            overflow: visible !important;
        }

        /* Fix text/image overlap inside content renderers */
        .stImage, .stMarkdown {
            margin-bottom: 1.5rem !important;
        }

        /* Ensure images and text are displayed as separate blocks */
        .stImage img {
            display: block;
            max-width: 100%;
            height: auto;
        }

        /* Give flashcards and mindmap outputs breathing space */
        .rendered-content {
            padding: 1rem;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            margin-bottom: 2rem;
            overflow: hidden;
        }
    </style>
""", unsafe_allow_html=True)

from datetime import datetime, timedelta
import calendar

def generate_activity_heatmap(quiz_history):
    """Generate a GitHub-style contribution heatmap with proper formatting"""
    
    # Get activity data
    activity_dates = {}
    if quiz_history:
        for quiz in quiz_history:
            date_key = quiz['date_taken'].strftime('%Y-%m-%d')
            activity_dates[date_key] = activity_dates.get(date_key, 0) + 1
    
    # Calculate date range (last 52 weeks)
    end_date = datetime.now()
    # Start from a Sunday to align with week structure
    start_date = end_date - timedelta(days=364)
    days_back = (start_date.weekday() + 1) % 7  # Adjust to previous Sunday
    start_date = start_date - timedelta(days=days_back)
    
    # Generate month labels
    month_labels = []
    month_positions = []
    current_month = None
    
    current_date = start_date
    week_index = 0
    
    while current_date <= end_date:
        month = current_date.month
        if month != current_month and current_date.day <= 7:
            current_month = month
            month_labels.append(calendar.month_abbr[month])
            month_positions.append(week_index)
        current_date += timedelta(days=7)
        week_index += 1
    
    total_weeks = week_index
    
    # Create month label HTML
    month_label_html = '<div style="display: flex; margin-bottom: 8px; padding-left: 35px; font-size: 0.75rem; color: #64748b;">'
    
    current_pos = 0
    for i, pos in enumerate(month_positions):
        if i > 0:
            # Add spacer
            spacer_weeks = pos - current_pos
            month_label_html += f'<div style="width: {spacer_weeks * 15}px;"></div>'
        month_label_html += f'<div style="min-width: 30px;">{month_labels[i]}</div>'
        current_pos = pos
    
    month_label_html += '</div>'
    
    # Generate heatmap HTML
    heatmap_html = '<div style="display: flex; gap: 3px; overflow-x: auto; padding: 10px 0;">'
    
    # Add day labels
    day_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    heatmap_html += '<div style="display: flex; flex-direction: column; gap: 3px; padding-right: 8px; justify-content: space-around;">'
    for i, day_label in enumerate(day_labels):
        # Only show Mon, Wed, Fri
        if i in [1, 3, 5]:
            heatmap_html += f'<div style="height: 13px; font-size: 0.65rem; color: #94a3b8; display: flex; align-items: center;">{day_label}</div>'
        else:
            heatmap_html += '<div style="height: 13px;"></div>'
    heatmap_html += '</div>'
    
    # Generate grid by weeks
    current_date = start_date
    while current_date <= end_date:
        heatmap_html += '<div style="display: flex; flex-direction: column; gap: 3px;">'
        
        # Generate 7 days for this week
        for day in range(7):
            cell_date = current_date + timedelta(days=day)
            
            # Don't show future dates
            if cell_date > end_date:
                heatmap_html += '<div style="width: 13px; height: 13px;"></div>'
                continue
            
            date_key = cell_date.strftime('%Y-%m-%d')
            activity_count = activity_dates.get(date_key, 0)
            
            # Determine color level
            if activity_count == 0:
                color = "#ebedf0"
            elif activity_count == 1:
                color = "#9be9a8"
            elif activity_count == 2:
                color = "#40c463"
            elif activity_count == 3:
                color = "#30a14e"
            else:
                color = "#216e39"
            
            tooltip = f"{cell_date.strftime('%b %d, %Y')}: {activity_count} {'activity' if activity_count == 1 else 'activities'}"
            
            heatmap_html += f'''
            <div style="
                width: 13px; 
                height: 13px; 
                background-color: {color}; 
                border-radius: 2px;
                border: 1px solid rgba(27,31,35,0.06);
            " title="{tooltip}"></div>
            '''
        
        heatmap_html += '</div>'
        current_date += timedelta(days=7)
    
    heatmap_html += '</div>'
    
    # Add legend
    current_year = datetime.now().year
    last_year = current_year - 1
    
    heatmap_html += f'''
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding: 0 35px;">
        <div style="display: flex; gap: 5px; align-items: center; font-size: 0.75rem; color: #64748b;">
            <span>Less</span>
            <div style="width: 13px; height: 13px; background-color: #ebedf0; border-radius: 2px; border: 1px solid rgba(27,31,35,0.06);"></div>
            <div style="width: 13px; height: 13px; background-color: #9be9a8; border-radius: 2px; border: 1px solid rgba(27,31,35,0.06);"></div>
            <div style="width: 13px; height: 13px; background-color: #40c463; border-radius: 2px; border: 1px solid rgba(27,31,35,0.06);"></div>
            <div style="width: 13px; height: 13px; background-color: #30a14e; border-radius: 2px; border: 1px solid rgba(27,31,35,0.06);"></div>
            <div style="width: 13px; height: 13px; background-color: #216e39; border-radius: 2px; border: 1px solid rgba(27,31,35,0.06);"></div>
            <span>More</span>
        </div>
        <div style="font-size: 0.8rem; color: #475569; font-weight: 500;">
            {last_year} - {current_year}
        </div>
    </div>
    '''
    
    return month_label_html, heatmap_html


# Usage in your dashboard (replace the heatmap generation section):
"""
# In Tab 1 of your show_dashboard function, replace the heatmap code with:

st.markdown('''
<div class="contribution-container">
    <div class="contribution-title">Your Learning Activity</div>
</div>
''', unsafe_allow_html=True)

month_labels, heatmap = generate_activity_heatmap(quiz_history)
st.markdown(month_labels, unsafe_allow_html=True)
st.markdown(heatmap, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
"""
def show_dashboard():
    """Renders the main student dashboard with enhanced UI."""
    user_id = st.session_state.user_id

    # Fetch all data once
    progress = db.get_user_progress(user_id)
    topics = db.get_topics_by_user(user_id)
    quiz_history = db.get_quiz_results_by_user(user_id)

    if not progress:
        st.error("Could not load user progress.")
        return

    # Calculate streak (simple example - days with quiz activity)
    from datetime import datetime, timedelta
    today = datetime.now().date()
    streak_days = 0
    if quiz_history:
        # Count consecutive days with activity
        activity_dates = sorted([q['date_taken'].date() for q in quiz_history], reverse=True)
        current_date = today
        for date in activity_dates:
            if date == current_date or date == current_date - timedelta(days=1):
                streak_days += 1
                current_date = date - timedelta(days=1)
            else:
                break

    # Header with streak badge
    st.markdown(f"""
    <div class="streak-badge">
        <span class="streak-icon">🔥</span>
        <span>{streak_days} Day Streak</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.title(f"Welcome, {st.session_state.username}!")

    tab1, tab2, tab3 = st.tabs(["Dashboard", "Topics", "Next Steps"])

    # Load and check weak topics data format
    is_old_data = False
    weak_topics_dict = {}
    weak_topics_data = json.loads(progress['weak_topics_list']) if progress.get('weak_topics_list') else {}

    if isinstance(weak_topics_data, list):
        is_old_data = True
    elif isinstance(weak_topics_data, dict):
        weak_topics_dict = weak_topics_data

    # --- Tab 1: Dashboard ---
    with tab1:
        # Contribution Heatmap
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h3 style="font-size: 1.1rem; font-weight: 600; color: #2d3748; margin-bottom: 1rem;">Your Learning Activity</h3>
        </div>
        """, unsafe_allow_html=True)

        # Generate heatmap data
        from datetime import datetime, timedelta
        import calendar

        # Get activity data
        activity_dates = {}
        if quiz_history:
            for quiz in quiz_history:
                date_key = quiz['date_taken'].strftime('%Y-%m-%d')
                activity_dates[date_key] = activity_dates.get(date_key, 0) + 1

        # Calculate date range - from January 1st to December 31st of current year
        current_year = datetime.now().year
        start_date = datetime(current_year, 1, 1)
        end_date = datetime(current_year, 12, 31)

        # Align start_date to Sunday (start of week)
        days_back = (start_date.weekday() + 1) % 7
        start_date = start_date - timedelta(days=days_back)

        # Calculate total weeks needed
        total_days = (end_date - start_date).days + 1
        total_weeks = (total_days + 6) // 7

        # Build month labels HTML
        month_html_parts = ['<div style="display: flex; margin-bottom: 8px; padding-left: 32px; gap: 0px;">']
        current_month = None
        weeks_in_month = {}

        for week in range(total_weeks):
            week_start = start_date + timedelta(days=week * 7)
            month = week_start.month
            
            if month not in weeks_in_month:
                weeks_in_month[month] = []
            weeks_in_month[month].append(week)

        # Generate month labels with proper spacing
        for month in range(1, 13):
            if month in weeks_in_month:
                week_count = len(weeks_in_month[month])
                width = week_count * 14  # 11px cell + 3px gap
                month_html_parts.append(f'<div style="min-width: {width}px; font-size: 0.7rem; color: #718096; font-weight: 500;">{calendar.month_abbr[month]}</div>')

        month_html_parts.append('</div>')
        month_labels_html = ''.join(month_html_parts)

        # Build main heatmap HTML
        heatmap_parts = [
            '<div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e2e8f0; overflow-x: auto;">',
            '<div style="display: flex; gap: 3px;">'
        ]

        # Day labels - ALL 7 days
        day_labels_order = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        heatmap_parts.append('<div style="display: flex; flex-direction: column; gap: 3px; padding-right: 8px; justify-content: flex-start;">')
        for i, label in enumerate(day_labels_order):
            # Show Mon, Wed, Fri labels only
            if i in [1, 3, 5]:
                heatmap_parts.append(f'<div style="height: 11px; font-size: 0.65rem; color: #94a3b8; display: flex; align-items: center; font-weight: 500; line-height: 11px;">{label}</div>')
            else:
                heatmap_parts.append('<div style="height: 11px;"></div>')
        heatmap_parts.append('</div>')

        # Generate week columns
        current_date_check = datetime.now()
        for week in range(total_weeks):
            heatmap_parts.append('<div style="display: flex; flex-direction: column; gap: 3px;">')
            
            # Generate ALL 7 days (Sunday to Saturday)
            for day in range(7):
                cell_date = start_date + timedelta(days=week * 7 + day)
                
                # Skip if before Jan 1 or after Dec 31 of current year
                if cell_date.year != current_year:
                    heatmap_parts.append('<div style="width: 11px; height: 11px;"></div>')
                    continue
                
                # Don't show future dates
                if cell_date > current_date_check:
                    heatmap_parts.append('<div style="width: 11px; height: 11px; background-color: transparent;"></div>')
                    continue
                
                date_key = cell_date.strftime('%Y-%m-%d')
                activity_count = activity_dates.get(date_key, 0)
                
                # Color scheme matching your app
                if activity_count == 0:
                    color = "#f1f5f9"
                    border_color = "#e2e8f0"
                elif activity_count == 1:
                    color = "#c7d2fe"
                    border_color = "#a5b4fc"
                elif activity_count == 2:
                    color = "#a78bfa"
                    border_color = "#8b5cf6"
                elif activity_count == 3:
                    color = "#7c3aed"
                    border_color = "#6d28d9"
                else:
                    color = "#5b21b6"
                    border_color = "#4c1d95"
                
                tooltip = f"{cell_date.strftime('%b %d, %Y')}: {activity_count} {'activity' if activity_count == 1 else 'activities'}"
                
                heatmap_parts.append(f'<div style="width: 11px; height: 11px; background-color: {color}; border-radius: 2px; border: 1px solid {border_color};" title="{tooltip}"></div>')
            
            heatmap_parts.append('</div>')

        heatmap_parts.append('</div>')  # Close flex container

        # Add legend
        heatmap_parts.append(f'''
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0;">
            <div style="display: flex; gap: 4px; align-items: center; font-size: 0.7rem; color: #64748b;">
                <span style="font-weight: 500;">Less</span>
                <div style="width: 11px; height: 11px; background-color: #f1f5f9; border-radius: 2px; border: 1px solid #e2e8f0;"></div>
                <div style="width: 11px; height: 11px; background-color: #c7d2fe; border-radius: 2px; border: 1px solid #a5b4fc;"></div>
                <div style="width: 11px; height: 11px; background-color: #a78bfa; border-radius: 2px; border: 1px solid #8b5cf6;"></div>
                <div style="width: 11px; height: 11px; background-color: #7c3aed; border-radius: 2px; border: 1px solid #6d28d9;"></div>
                <div style="width: 11px; height: 11px; background-color: #5b21b6; border-radius: 2px; border: 1px solid #4c1d95;"></div>
                <span style="font-weight: 500;">More</span>
            </div>
            <div style="font-size: 0.75rem; color: #475569; font-weight: 600;">
                {current_year}
            </div>
        </div>
        </div>
        ''')

        heatmap_html = ''.join(heatmap_parts)

        # Render the heatmap with unsafe_allow_html=True
        st.markdown(month_labels_html, unsafe_allow_html=True)
        st.markdown(heatmap_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
                

        
        col1, col2 = st.columns([1, 1.2])

        with col1:
            # Topics Covered Card
            st.markdown("""
            <div style="margin-bottom: 30px;">
                <h3 style="color: #1a202c; font-weight: 700; font-size: 1.5rem; margin-bottom: 20px;">Topics Covered</h3>
            </div>
            """, unsafe_allow_html=True)
            
            with st.container(border=True):
                if not topics:
                    st.info("Start a new topic to see your progress!")
                else:
                    for idx, topic in enumerate(topics):
                        topic_quiz_data = db.get_quiz_results_by_topic(user_id, topic['topic_id'])
                        best_score = max([float(q['score']) for q in topic_quiz_data]) if topic_quiz_data else 0.0
                        
                        # Create a styled topic item
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                            border-radius: 12px;
                            padding: 20px;
                            margin-bottom: 15px;
                            border-left: 4px solid #5b6fd8;
                        ">
                            <div style="
                                font-size: 1.1rem;
                                font-weight: 600;
                                color: #1a202c;
                                margin-bottom: 12px;
                            ">{topic['topic_name']}</div>
                            <div style="
                                display: flex;
                                align-items: center;
                                justify-content: space-between;
                                margin-bottom: 8px;
                            ">
                                <span style="color: #4a5568; font-size: 0.9rem; font-weight: 500;">Mastery Level</span>
                                <span style="color: #5b6fd8; font-weight: 700; font-size: 1.1rem;">{int(best_score)}%</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.progress(best_score / 100)
                        
                        if idx < len(topics) - 1:
                            st.markdown("<br>", unsafe_allow_html=True)

            # Weak Topics Card
            st.markdown("""
            <div style="margin: 30px 0 20px 0;">
                <h3 style="color: #1a202c; font-weight: 700; font-size: 1.5rem;">Weak Topics</h3>
            </div>
            """, unsafe_allow_html=True)
            
            with st.container(border=True):
                if is_old_data:
                    st.markdown("""
                    <div style="
                        background-color: #fef3c7;
                        border-left: 4px solid #f59e0b;
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 15px;
                    ">
                        <p style="color: #92400e; margin: 0;">⚠️ Your weak topics list uses an old format. Please retake quizzes to update.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    for topic_name in weak_topics_data:
                        st.markdown(f"• {topic_name}")
                
                elif weak_topics_dict:
                    st.markdown("""
                    <div style="
                        background-color: #dbeafe;
                        border-left: 4px solid #3b82f6;
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    ">
                        <p style="color: #1e40af; margin: 0; font-weight: 500;">💡 Click a sub-topic to start a focused review.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for main_topic_name, sub_topics in weak_topics_dict.items():
                        st.markdown(f"""
                        <div style="
                            color: #2d3748;
                            font-weight: 600;
                            font-size: 1rem;
                            margin: 20px 0 12px 0;
                            padding-bottom: 8px;
                            border-bottom: 2px solid #e2e8f0;
                        ">From Topic: {main_topic_name}</div>
                        """, unsafe_allow_html=True)
                        
                        for sub_topic_name in sub_topics:
                            col_btn = st.columns([1])[0]
                            with col_btn:
                                if st.button(
                                    f"📖 Review: {sub_topic_name}", 
                                    key=f"dash_weak_{main_topic_name}_{sub_topic_name}", 
                                    use_container_width=True,
                                    type="secondary"
                                ):
                                    topic_data = db.get_topic_by_name(user_id, main_topic_name)
                                    if topic_data:
                                        st.session_state.current_topic_id = topic_data['topic_id']
                                        st.session_state.current_summary = topic_data['content_summary']
                                        st.session_state.current_topic_name_to_review = sub_topic_name
                                        st.session_state.focused_review = None
                                        st.session_state.page = "review_topic"
                                        st.rerun()
                                    else:
                                        st.error(f"Could not find data for topic: {main_topic_name}")
                else:
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                        border-left: 4px solid #10b981;
                        padding: 25px;
                        border-radius: 12px;
                        text-align: center;
                    ">
                        <div style="font-size: 2.5rem; margin-bottom: 10px;">🎉</div>
                        <div style="color: #065f46; font-weight: 600; font-size: 1.1rem;">No weak topics identified!</div>
                        <div style="color: #047857; font-size: 0.95rem; margin-top: 8px;">You're doing great! Keep up the excellent work.</div>
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            # Progress Chart Card - SINGLE INSTANCE
            st.markdown("""
            <div style="margin-bottom: 20px;">
                <h3 style="color: #1a202c; font-weight: 700; font-size: 1.5rem;">Progress</h3>
            </div>
            """, unsafe_allow_html=True)
            
            with st.container(border=True):
                if quiz_history:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=[q['date_taken'] for q in quiz_history],
                        y=[float(q['score']) for q in quiz_history],
                        mode='lines+markers',
                        line=dict(color='#5b6fd8', width=3),
                        marker=dict(size=8, color='#5b6fd8'),
                        fill='tozeroy',
                        fillcolor='rgba(91, 111, 216, 0.1)'
                    ))
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Score (%)",
                        yaxis_range=[0, 100],
                        plot_bgcolor='#f7fafc',
                        paper_bgcolor='white',
                        font=dict(family='Inter', color='#2d3748'),
                        margin=dict(l=40, r=20, t=20, b=40),
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Metrics with better styling
                    st.markdown("<br>", unsafe_allow_html=True)
                    mcol1, mcol2 = st.columns(2)
                    
                    avg_score = float(progress.get('average_score', 0))
                    
                    with mcol1:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 20px;
                            border-radius: 12px;
                            text-align: center;
                        ">
                            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 5px;">Average Score</div>
                            <div style="font-size: 2rem; font-weight: 700;">{avg_score:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with mcol2:
                        if len(quiz_history) > 1:
                            last_score = float(quiz_history[-1]['score'])
                            improvement = last_score - avg_score
                            color = "#10b981" if improvement >= 0 else "#ef4444"
                            arrow = "↑" if improvement >= 0 else "↓"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
                                color: white;
                                padding: 20px;
                                border-radius: 12px;
                                text-align: center;
                            ">
                                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 5px;">Improvement</div>
                                <div style="font-size: 2rem; font-weight: 700;">{arrow} {abs(improvement):.1f}%</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="
                                background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
                                color: white;
                                padding: 20px;
                                border-radius: 12px;
                                text-align: center;
                            ">
                                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 5px;">Improvement</div>
                                <div style="font-size: 2rem; font-weight: 700;">N/A</div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Take a quiz to see your progress chart.")

            # Next Steps Card
            st.markdown("""
            <div style="margin: 30px 0 20px 0;">
                <h3 style="color: #1a202c; font-weight: 700; font-size: 1.5rem;">Next Steps</h3>
            </div>
            """, unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("""
                <div style="
                    color: #4a5568;
                    font-size: 1rem;
                    margin-bottom: 20px;
                    text-align: center;
                ">What would you like to do next?</div>
                """, unsafe_allow_html=True)
                
                # Create two equal columns for buttons
                bcol1, bcol2 = st.columns(2)
                
                with bcol1:
                    if st.button("Start New Topic", type="primary", use_container_width=True, key="next_new_topic"):
                        st.session_state.page = "onboarding_start"
                        st.rerun()
                
                with bcol2:
                    if st.button("Review Topics", key="review_topics_btn", use_container_width=True, type="secondary"):
                        st.info("Click the 'Topics' tab above to review your learning materials.")

        
            
    # --- Tab 2: Topics ---
    with tab2:
        st.subheader("Your Learning History (Per-Topic Details)")
        
        if not topics:
            st.info("You haven't started any topics yet. Click 'Start New Topic'!")
            return

        for topic in topics:
            # Get topic data
            content = db.get_topic_content(topic['topic_id'])
            topic_quiz_history = db.get_quiz_results_by_topic(user_id, topic['topic_id'])
            
            # Calculate scores - convert Decimal to float
            if topic_quiz_history:
                scores = [float(q['score']) for q in topic_quiz_history]
                avg_score = sum(scores) / len(scores)
                best_score = max(scores)
            else:
                avg_score = 0.0
                best_score = 0.0
            
            # Topic Card
            st.markdown(f"""
            <div class="topic-card">
                <div class="topic-title">{topic['topic_name']}</div>
                <div class="topic-date">Started: {topic['date_created'].strftime('%Y-%m-%d')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Topic-Specific Progress
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="progress-section">
                    <div class="progress-label">
                        <span>Topic-Specific Progress</span>
                        <span style="font-weight: 700; color: #1a202c;">""" + f"{int(avg_score)}%" + """</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.progress(avg_score / 100)
                st.caption(f"0%{' ' * 150}100%")
            
            with col2:
                st.markdown("""
                <div class="progress-section">
                    <div class="progress-label">
                        <span>Best Score</span>
                        <span style="font-weight: 700; color: #1a202c;">""" + f"{int(best_score)}%" + """</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.progress(best_score / 100)
                st.caption(f"0%{' ' * 150}100%")
            
            # Check for missing materials
            missing_mindmap = not content.get('mindmap')
            missing_flashcards = not content.get('flashcards')
            missing_formula_sheet = not content.get('formula_sheet')

            if (missing_mindmap or missing_flashcards or missing_formula_sheet) and content.get('summary'):
                st.warning("This topic is missing some generated materials.")
                if st.button("✨ Generate Missing Content", key=f"gen_{topic['topic_id']}"):
                    with st.spinner("Generating new materials..."):
                        summary_text = content['summary']
                        if missing_mindmap:
                            new_mindmap = generative_ai.generate_mindmap_markdown(summary_text)
                            if new_mindmap: db.save_mindmap(topic['topic_id'], new_mindmap)
                        if missing_flashcards:
                            new_flashcards = generative_ai.generate_flashcards(summary_text)
                            if new_flashcards: db.save_flashcards(topic['topic_id'], new_flashcards)
                        if missing_formula_sheet:
                            new_formula_sheet = generative_ai.generate_formula_sheet(summary_text)
                            if new_formula_sheet: db.save_formula_sheet(topic['topic_id'], new_formula_sheet)
                    st.success("Materials generated!")
                    st.rerun()
            
            # Material Buttons
            st.markdown("---")
            bcol1, bcol2, bcol3, bcol4 = st.columns(4)
            
            if bcol1.button("View Summary", key=f"summary_{topic['topic_id']}", use_container_width=True):
                st.session_state.view_topic = topic['topic_id']
                st.session_state.view_content_type = 'summary'
            
            if bcol2.button("View Mind Map", key=f"mindmap_{topic['topic_id']}", use_container_width=True):
                st.session_state.view_topic = topic['topic_id']
                st.session_state.view_content_type = 'mindmap'
            
            if bcol3.button("View Flashcards", key=f"flashcards_{topic['topic_id']}", use_container_width=True):
                st.session_state.view_topic = topic['topic_id']
                st.session_state.view_content_type = 'flashcards'
            
            if bcol4.button("Formula Sheet", key=f"formula_{topic['topic_id']}", use_container_width=True):
                st.session_state.view_topic = topic['topic_id']
                st.session_state.view_content_type = 'formula_sheet'

            # Display selected content
            if st.session_state.get('view_topic') == topic['topic_id']:
                st.markdown("---")
                content_type = st.session_state.get('view_content_type')

                with st.container(border=True):
                    if content_type == 'summary':
                        st.markdown(content['summary'] if content['summary'] else "No summary available.")
                    elif content_type == 'mindmap':
                        if content['mindmap']:
                            render_markmap_html(content['mindmap'])
                        else:
                            st.warning("No mindmap available.")
                    elif content_type == 'flashcards':
                        if content['flashcards']:
                            render_flashcards(content['flashcards'])
                        else:
                            st.warning("No flashcards available.")
                    elif content_type == 'formula_sheet':
                        st.markdown(content['formula_sheet'] if content['formula_sheet'] else "No formulas found.")

            st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Tab 3: Next Steps ---
    # Replace the "Tab 3: Next Steps" section in dashboard.py with this:

    # --- Tab 3: Next Steps ---
    with tab3:
        st.markdown("## Next Steps")
        
        # Load and check weak topics data format
        is_old_data = False
        weak_topics_dict = {}
        weak_topics_data = json.loads(progress['weak_topics_list']) if progress.get('weak_topics_list') else {}

        if isinstance(weak_topics_data, list):
            is_old_data = True
        elif isinstance(weak_topics_data, dict):
            weak_topics_dict = weak_topics_data

        # Updated compact CSS
        st.markdown("""
        <style>
        .next-steps-warning {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            font-size: 0.95rem;
            color: #856404;
        }
        
        .topic-section {
            margin-bottom: 25px;
        }
        
        .topic-header {
            font-size: 1.4rem;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 15px;
        }
        
        .success-message {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            border-radius: 8px;
            font-size: 0.95rem;
            color: #155724;
            text-align: center;
        }
        
        /* Compact button styling for Next Steps tab specifically */
        div[data-testid="column"] button[kind="secondary"] {
            background: linear-gradient(135deg, #0d98ba 0%, #0a7a96 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 15px 18px !important;
            min-height: 60px !important;
            max-height: 80px !important;
            height: auto !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            line-height: 1.3 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            white-space: normal !important;
            word-wrap: break-word !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        div[data-testid="column"] button[kind="secondary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
            background: linear-gradient(135deg, #0a7a96 0%, #085c73 100%) !important;
        }
        
        div[data-testid="column"] button[kind="secondary"] div[data-testid="stMarkdownContainer"] p {
            font-size: 0.95rem !important;
            line-height: 1.3 !important;
            margin: 0 !important;
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        if is_old_data:
            st.markdown("""
            <div class="next-steps-warning">
                ⚠️ Your weak topics list uses an old format. Please retake quizzes to update.
            </div>
            """, unsafe_allow_html=True)
            
            for topic_name in weak_topics_data:
                st.markdown(f"- {topic_name}")
                
        elif weak_topics_dict:
            st.markdown("""
            <div class="next-steps-warning">
                💡 Focus on reviewing your weak topics below:
            </div>
            """, unsafe_allow_html=True)
            
            # Group by main topic
            for main_topic_name, sub_topics in weak_topics_dict.items():
                st.markdown(f"""
                <div class="topic-section">
                    <h2 class="topic-header">{main_topic_name}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Create cards in a 3-column grid
                cols = st.columns(3)
                for idx, sub_topic_name in enumerate(sub_topics):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        unique_key = f"nextstep_{main_topic_name}_{sub_topic_name}_{idx}"
                        if st.button(sub_topic_name, key=unique_key, use_container_width=True):
                            topic_data = db.get_topic_by_name(user_id, main_topic_name)
                            if topic_data:
                                st.session_state.current_topic_id = topic_data['topic_id']
                                st.session_state.current_summary = topic_data['content_summary']
                                st.session_state.current_topic_name_to_review = sub_topic_name
                                st.session_state.focused_review = None
                                st.session_state.page = "review_topic"
                                st.rerun()
                            else:
                                st.error(f"Could not find data for topic: {main_topic_name}")
        else:
            st.markdown("""
            <div class="success-message">
                🎉 You're doing great! No weak topics identified.<br>
                Try starting a new topic to expand your knowledge.
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Start New Topic", type="primary", use_container_width=True):
                    st.session_state.page = "onboarding_start"
                    st.rerun()
