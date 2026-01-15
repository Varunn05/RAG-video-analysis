import streamlit as st
import json
import os
from youtube_transcript_api import YouTubeTranscriptApi
import plotly.graph_objects as go
import re
from main import extract_claims, fact_check_all_claims

# Page config
st.set_page_config(
    page_title="YouTube Fact-Checker",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .claim-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    .claim-card-true {
        background-color: #d4edda;
        border-color: #28a745;
    }
    .claim-card-false {
        background-color: #f8d7da;
        border-color: #dc3545;
    }
    .claim-card-misleading {
        background-color: #fff3cd;
        border-color: #ffc107;
    }
    .claim-card-unverifiable {
        background-color: #e2e3e5;
        border-color: #6c757d;
    }
    .timestamp-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        background-color: #007bff;
        color: white;
        font-weight: bold;
        font-size: 0.875rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'video_id' not in st.session_state:
    st.session_state['video_id'] = None
if 'timestamp' not in st.session_state:
    st.session_state['timestamp'] = 0
if 'filter' not in st.session_state:
    st.session_state['filter'] = 'All'
if 'report_data' not in st.session_state:
    st.session_state['report_data'] = None
if 'processing' not in st.session_state:
    st.session_state['processing'] = False


# ============================================================================
# UI Helper Functions (merged from ui_helpers.py)
# ============================================================================

def load_fact_check_report(filepath="fact_checked_report.json"):
    """Load the fact-checked report from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def calculate_trust_score(summary):
    """Calculate overall trust score (0-100) based on verdict distribution."""
    total = summary.get('total_claims', 0)
    if total == 0:
        return 0
    
    true_count = summary.get('true', 0)
    misleading_count = summary.get('misleading', 0)
    
    score = ((true_count + 0.5 * misleading_count) / total) * 100
    return round(score, 1)


def get_trust_level(score):
    """Get trust level category based on score."""
    if score >= 80:
        return ("Highly Trustworthy", "#28a745")  # Green
    elif score >= 60:
        return ("Mostly Accurate", "#90ee90")  # Light green
    elif score >= 40:
        return ("Mixed Accuracy", "#ffc107")  # Yellow
    elif score >= 20:
        return ("Low Accuracy", "#ff8c00")  # Orange
    else:
        return ("High Misinformation", "#dc3545")  # Red


def filter_claims(claims, filter_type):
    """Filter claims by verdict type."""
    if filter_type == 'All':
        return claims
    
    return [c for c in claims if c.get('status') == filter_type]


def parse_timestamp(timestamp_str):
    """Convert timestamp string to seconds."""
    if not timestamp_str:
        return 0
    
    # Handle "123.45s" format
    if 's' in timestamp_str:
        try:
            return int(float(timestamp_str.replace('s', '')))
        except ValueError:
            return 0
    
    # Handle "MM:SS" or "HH:MM:SS" format
    if ':' in timestamp_str:
        parts = timestamp_str.split(':')
        try:
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except ValueError:
            return 0
    
    return 0


def format_timestamp(seconds):
    """Convert seconds to MM:SS format."""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"


def create_youtube_embed_url(video_id, start_time=0):
    """Generate YouTube embed URL with timestamp."""
    if start_time > 0:
        return f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1"
    return f"https://www.youtube.com/embed/{video_id}"


def extract_video_id(url):
    """Extract YouTube video ID from URL."""
    pattern = r'(?:youtu\.be/|youtube\.com/watch\?v=|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def get_status_emoji(status):
    """Get emoji for claim status."""
    emoji_map = {
        'TRUE': '✅',
        'FALSE': '❌',
        'MISLEADING': '⚠️',
        'UNVERIFIABLE': '❓',
        'ERROR': '⚡'
    }
    return emoji_map.get(status, '❔')


def get_status_color(status):
    """Get color for claim status."""
    color_map = {
        'TRUE': '#28a745',      # Green
        'FALSE': '#dc3545',     # Red
        'MISLEADING': '#ffc107', # Yellow
        'UNVERIFIABLE': '#6c757d', # Gray
        'ERROR': '#fd7e14'      # Orange
    }
    return color_map.get(status, '#6c757d')


def format_transcript(transcript_list):
    """Format transcript with timestamps"""
    formatted_text = ""
    buffer_text = ""
    buffer_start = None

    for line in transcript_list:
        text = line['text'] if isinstance(line, dict) else line.text
        start = line['start'] if isinstance(line, dict) else line.start
        
        if buffer_start is None:
            buffer_start = start

        buffer_text += " " + text.strip()

        if text.strip().endswith(('.', '?', '!')):
            formatted_text += f"[{buffer_start:.2f}s]{buffer_text}\n"
            buffer_text = ""
            buffer_start = None
            
    if buffer_text:
         formatted_text += f"[{buffer_start:.2f}s]{buffer_text}\n"
         
    return formatted_text


def create_gauge_chart(score):
    """Create a gauge chart for the trust score"""
    level_name, color = get_trust_level(score)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Truthometer", 'font': {'size': 24}},
        delta={'reference': 50, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 20], 'color': '#ffcccc'},
                {'range': [20, 40], 'color': '#ffe6cc'},
                {'range': [40, 60], 'color': '#ffffcc'},
                {'range': [60, 80], 'color': '#e6ffcc'},
                {'range': [80, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig


def render_claim_card(claim, index):
    """Render a single claim card with all interactive elements"""
    status = claim.get('status', 'UNVERIFIABLE')
    timestamp = claim.get('timestamp', '0s')
    claim_text = claim.get('claim', '')
    explanation = claim.get('explanation', '')
    confidence = claim.get('confidence', 'N/A')
    sources = claim.get('sources', [])
    
    # Get styling
    emoji = get_status_emoji(status)
    color = get_status_color(status)
    
    # Parse timestamp
    seconds = parse_timestamp(timestamp)
    formatted_time = format_timestamp(seconds)
    
    # Card container
    with st.container():
        # Header with timestamp and status
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            st.markdown(f'<span class="timestamp-badge">{formatted_time}</span>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**{emoji} {status}** ({confidence} confidence)")
        
        with col3:
            if st.button("▶ Jump", key=f"jump_{index}", use_container_width=True):
                st.session_state['timestamp'] = seconds
                st.rerun()
        
        # Claim text
        st.markdown(f"**Claim:** {claim_text}")
        
        # Explanation
        st.markdown(f"*{explanation}*")
        
        # Deep dive expander
        with st.expander("View Evidence & Sources"):
            if sources:
                st.markdown("### Evidence from Web Sources:")
                for i, source in enumerate(sources, 1):
                    st.markdown(f"**Source {i}: [{source.get('title', 'Unknown')}]({source.get('url', '#')})**")
                    st.markdown(f"> {source.get('snippet', 'No snippet available')}")
                    st.markdown("---")
            else:
                st.info("No sources available for this claim.")
        
        st.markdown("---")


# Main UI
st.title("YouTube Fact-Checker Dashboard")
st.markdown("Analyze YouTube videos for factual accuracy using AI-powered fact-checking.")

# Input section
url = st.text_input("Enter YouTube Video URL:", placeholder="")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Analyze Video", type="primary", use_container_width=True):
        if url:
            video_id = extract_video_id(url)
            
            if video_id:
                st.session_state['video_id'] = video_id
                st.session_state['processing'] = True
                
                with st.spinner("Fetching transcript..."):
                    try:
                        # Use the correct API - fetch() method
                        api = YouTubeTranscriptApi()
                        transcript_list = api.fetch(
                            video_id, 
                            languages=['en', 'en-IN', 'hi']
                        )
                        
                        final_transcript = format_transcript(transcript_list)
                        
                        with open("transcript.txt", "w", encoding="utf-8") as f:
                            f.write(final_transcript)
                        
                        st.success("Transcript fetched!")
                        
                    except Exception as e:
                        st.error(f"Error fetching transcript: {e}")
                        st.session_state['processing'] = False
                        st.stop()
                
                with st.spinner("Extracting claims..."):
                    try:
                        claims = extract_claims("transcript.txt")
                        with open("claims.json", 'w', encoding='utf-8') as f:
                            json.dump(claims, f, indent=2, ensure_ascii=False)
                        st.success(f"Extracted {len(claims)} claims!")
                    except Exception as e:
                        st.error(f"Error extracting claims: {e}")
                        st.session_state['processing'] = False
                        st.stop()
                
                with st.spinner("Fact-checking claims... This may take a few minutes."):
                    try:
                        report = fact_check_all_claims()
                        st.session_state['report_data'] = report
                        st.success("Fact-checking complete!")
                        st.session_state['processing'] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error fact-checking: {e}")
                        st.session_state['processing'] = False
                        st.stop()
            else:
                st.error("Invalid YouTube URL format")
        else:
            st.warning("Please enter a YouTube URL first")

with col2:
    if st.button("Load Existing Report", use_container_width=True):
        report = load_fact_check_report()
        if report:
            st.session_state['report_data'] = report
            st.success("Report loaded!")
            st.rerun()
        else:
            st.error("No fact-checked report found. Please analyze a video first.")

# Display results if report exists
if st.session_state['report_data']:
    report = st.session_state['report_data']
    summary = report.get('summary', {})
    claims = report.get('claims', [])
    
    st.markdown("---")
    
    # Two-column layout
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        st.markdown("### Video Player")
        
        # Video player
        if st.session_state['video_id']:
            video_url = create_youtube_embed_url(
                st.session_state['video_id'], 
                st.session_state['timestamp']
            )
            
            st.markdown(
                f'<iframe width="100%" height="400" src="{video_url}" '
                f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
                f'encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
                unsafe_allow_html=True
            )
        else:
            st.info("Video will appear here after analysis")
        
        # Truthometer
        st.markdown("### Truthometer")
        trust_score = calculate_trust_score(summary)
        level_name, _ = get_trust_level(trust_score)
        
        gauge_chart = create_gauge_chart(trust_score)
        st.plotly_chart(gauge_chart, use_container_width=True)
        
        st.markdown(f"**Overall Assessment:** {level_name}")
        
        # Summary stats
        st.markdown("### Summary Statistics")
        stat_col1, stat_col2 = st.columns(2)
        
        with stat_col1:
            st.metric("Total Claims", summary.get('total_claims', 0))
            st.metric("✅ True", summary.get('true', 0))
            st.metric("⚠️Misleading", summary.get('misleading', 0))
        
        with stat_col2:
            st.metric("✅ Trust Score", f"{trust_score}%")
            st.metric("❌ False", summary.get('false', 0))
            st.metric("❓ Unverifiable", summary.get('unverifiable', 0))
    
    with right_col:
        st.markdown("### Fact-Checked Claims")
        
        # Filter pills
        st.markdown("**Filter by:**")
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
        
        with filter_col1:
            if st.button(f"All ({summary.get('total_claims', 0)})", use_container_width=True):
                st.session_state['filter'] = 'All'
                st.rerun()
        
        with filter_col2:
            if st.button(f"✅ True ({summary.get('true', 0)})", use_container_width=True):
                st.session_state['filter'] = 'TRUE'
                st.rerun()
        
        with filter_col3:
            if st.button(f"❌ False ({summary.get('false', 0)})", use_container_width=True):
                st.session_state['filter'] = 'FALSE'
                st.rerun()
        
        with filter_col4:
            if st.button(f"⚠️ Misleading ({summary.get('misleading', 0)})", use_container_width=True):
                st.session_state['filter'] = 'MISLEADING'
                st.rerun()
        
        with filter_col5:
            if st.button(f"❓ Unverifiable ({summary.get('unverifiable', 0)})", use_container_width=True):
                st.session_state['filter'] = 'UNVERIFIABLE'
                st.rerun()
        
        st.markdown(f"**Showing: {st.session_state['filter']}**")
        st.markdown("---")
        
        # Filter and display claims
        filtered_claims = filter_claims(claims, st.session_state['filter'])
        
        if filtered_claims:
            # Scrollable container for claims
            for i, claim in enumerate(filtered_claims):
                render_claim_card(claim, i)
        else:
            st.info(f"No claims found with status: {st.session_state['filter']}")

else:
    st.info("Enter a YouTube URL and click 'Analyze Video' to get started, or load an existing report.")