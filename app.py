import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from agents import create_crew
from tools import (
    fetch_aqhi_data,
    fetch_individual_pollutants,
    fetch_aqhi_historical_trend,
    fetch_weather_data,
    fetch_pollen_data
)

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Ottawa Environmental Health Monitor",
    page_icon="🌳",
    layout="wide"
)

st.title("🌳 Ottawa Environmental Health Monitor")
st.markdown("""
Advanced multi-source environmental health intelligence with real-time pollutant analysis 
and 3-day air quality trends for Ottawa.
""")

# Initialize session state
if "result" not in st.session_state:
    st.session_state.result = ""
if "logs" not in st.session_state:
    st.session_state.logs = ""
if "raw_data" not in st.session_state:
    st.session_state.raw_data = None

# --- Sidebar Controls ---
with st.sidebar:
    st.header("🔑 API Configuration")
    
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys",
        placeholder="sk-..."
    )
    
    if not api_key:
        st.warning("⚠️ Please enter your OpenAI API key to continue")
    else:
        st.success("✅ API key provided")
    
    st.divider()
    st.header("⚙️ Controls")
    
    if st.button("🔄 Generate Daily Brief", use_container_width=True, disabled=not api_key):
        st.session_state.result = ""
        st.session_state.raw_data = None
        
        # Fetch all data
        with st.spinner("📊 Fetching environmental data from 4 sources..."):
            aqhi = fetch_aqhi_data()
            pollutants = fetch_individual_pollutants()
            trend = fetch_aqhi_historical_trend()
            weather = fetch_weather_data()
            pollen = fetch_pollen_data()
            
            st.session_state.raw_data = {
                "aqhi": aqhi,
                "pollutants": pollutants,
                "trend": trend,
                "weather": weather,
                "pollen": pollen
            }
        
        # Run crew with user's API key and fetched data
        with st.spinner("🤖 AI agents analyzing data..."):
            try:
                import io
                import os
                from contextlib import redirect_stdout
                
                # Set API key as environment variable for LangChain
                os.environ["OPENAI_API_KEY"] = api_key
                
                # Pass the actual fetched data to the crew
                health_crew = create_crew(api_key=api_key)
                
                f = io.StringIO()
                with redirect_stdout(f):
                    result = health_crew.kickoff(inputs={
                        'aqhi_data': aqhi,
                        'pollutants_data': pollutants,
                        'trend_data': trend,
                        'weather_data': weather,
                        'pollen_data': pollen
                    })
                
                st.session_state.logs = f.getvalue()
                st.session_state.result = result
                
                st.success("✅ Brief generated successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    st.divider()
    st.markdown("### 📡 Data Sources")
    st.markdown("""
    - **AQHI**: Environment Canada
    - **Pollutants**: Air Quality Ontario
    - **Trends**: Historical AQHI (3-day)
    - **Weather**: Open-Meteo
    - **Pollen**: Seasonal Data
    """)

# --- Main Content Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Daily Brief", "📊 Live Data", "📈 Trends", "🤖 AI Agents", "🔧 Logs"])

# Tab 1: Daily Brief
with tab1:
    st.header("Daily Environmental Health Brief")
    
    if st.session_state.result:
        st.markdown(st.session_state.result)
    else:
        st.info("👈 Click 'Generate Daily Brief' in the sidebar to create today's assessment")

# Tab 2: Live Data
with tab2:
    st.header("Real-Time Environmental Data")
    
    if st.session_state.raw_data:
        # Row 1: AQHI + Pollutants
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌍 Air Quality Index (AQHI)")
            if st.session_state.raw_data["aqhi"]["status"] == "success":
                aqhi = st.session_state.raw_data["aqhi"]
                st.metric("AQHI Value", aqhi["aqhi_value"], help="1-10+ scale")
                st.metric("Risk Level", aqhi["risk_level"])
                st.caption(f"📍 {aqhi['station_name']}")
                st.caption(f"⏰ {aqhi['timestamp']}")
            else:
                st.error(st.session_state.raw_data["aqhi"]["message"])
        
        with col2:
            st.subheader("⚠️ Individual Pollutants")
            if st.session_state.raw_data["pollutants"]["status"] == "success":
                pol = st.session_state.raw_data["pollutants"]
                
                col2a, col2b, col2c = st.columns(3)
                with col2a:
                    st.metric("PM2.5", f"{pol['pm25']} µg/m³", 
                             help="WHO safe: 12 µg/m³")
                with col2b:
                    st.metric("O3", f"{pol['o3']} ppb", 
                             help="Respiratory irritant")
                with col2c:
                    st.metric("NO2", f"{pol['no2']} ppb", 
                             help="Airway irritant")
                
                st.caption(f"📍 {pol['station']}")
                st.caption(f"⏰ {pol['timestamp']}")
            else:
                st.warning(st.session_state.raw_data["pollutants"]["message"])
        
        st.divider()
        
        # Row 2: Weather + Pollen
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("🌤️ Weather Conditions")
            if st.session_state.raw_data["weather"]["status"] == "success":
                weather = st.session_state.raw_data["weather"]
                st.metric("Temperature", f"{weather['temperature_celsius']}°C")
                st.metric("Humidity", f"{weather['relative_humidity']}%")
                st.metric("Wind Speed", f"{weather['wind_speed_kmh']} km/h")
                st.caption(weather['weather_condition'])
            else:
                st.error(st.session_state.raw_data["weather"]["message"])
        
        with col4:
            st.subheader("🌾 Pollen Levels")
            if st.session_state.raw_data["pollen"]["status"] == "success":
                pollen = st.session_state.raw_data["pollen"]
                st.metric("Tree Pollen", pollen["tree_pollen"])
                st.metric("Grass Pollen", pollen["grass_pollen"])
                st.metric("Weed Pollen", pollen["weed_pollen"])
                st.caption(f"Month: {pollen['month']}")
            else:
                st.error(st.session_state.raw_data["pollen"]["message"])
        
        st.divider()
        
        # Raw JSON
        st.subheader("📋 Raw API Data (JSON)")
        
        col_aqhi, col_pol, col_weather, col_pollen = st.columns(4)
        
        with col_aqhi:
            st.caption("AQHI")
            st.json(st.session_state.raw_data["aqhi"])
        
        with col_pol:
            st.caption("Pollutants")
            st.json(st.session_state.raw_data["pollutants"])
        
        with col_weather:
            st.caption("Weather")
            st.json(st.session_state.raw_data["weather"])
        
        with col_pollen:
            st.caption("Pollen")
            st.json(st.session_state.raw_data["pollen"])
    
    else:
        st.info("👈 Click 'Generate Daily Brief' to fetch live data")

# Tab 3: Trends
with tab3:
    st.header("3-Day AQHI Trend Analysis")
    
    if st.session_state.raw_data and st.session_state.raw_data["trend"]["status"] == "success":
        trend = st.session_state.raw_data["trend"]
        
        # Trend metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current AQHI", f"{trend['current_aqhi']:.1f}")
        with col2:
            st.metric("Average AQHI", f"{trend['average_aqhi']:.1f}")
        with col3:
            st.metric("Peak AQHI", f"{trend['max_aqhi']:.1f}")
        with col4:
            trend_color = "🔴" if trend["trend"] == "increasing" else "🟢" if trend["trend"] == "decreasing" else "🟡"
            st.metric("Trend", f"{trend_color} {trend['trend'].title()}", 
                     delta=f"{trend['change_percent']:.1f}%")
        
        st.caption(f"Data Range: {trend['time_range']}")
        st.caption(f"Data Points: {trend['data_points']} observations")
        
        st.divider()
        
        # Time series plot
        if len(trend['timestamps']) > 0:
            st.subheader("📈 AQHI Time Series (Last 3 Days)")
            
            # Create DataFrame
            df = pd.DataFrame({
                'Time': pd.to_datetime(trend['timestamps']),
                'AQHI': trend['aqhi_values']
            })
            
            # Create plot
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(df['Time'], df['AQHI'], marker='o', linestyle='-', linewidth=2, markersize=4, color='#1f77b4')
            
            # Add risk threshold lines
            ax.axhline(y=3, color='green', linestyle='--', alpha=0.5, label='Low Risk (1-3)')
            ax.axhline(y=6, color='orange', linestyle='--', alpha=0.5, label='Moderate (4-6)')
            ax.axhline(y=10, color='red', linestyle='--', alpha=0.5, label='High (7+)')
            
            ax.set_xlabel('Time')
            ax.set_ylabel('AQHI Value')
            ax.set_title('AQHI 3-Day Time Series')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # Key insights
            st.subheader("📌 Trend Insights")
            
            if trend['trend'] == 'increasing':
                st.warning(f"⚠️ **Air quality is WORSENING** (+{abs(trend['change_percent']):.1f}% over 3 days)")
                st.write("- Consider increasing indoor activity")
                st.write("- Monitor forecasts for further deterioration")
            elif trend['trend'] == 'decreasing':
                st.success(f"✅ **Air quality is IMPROVING** ({trend['change_percent']:.1f}% over 3 days)")
                st.write("- Outdoor activities becoming safer")
                st.write("- Trend likely to continue")
            elif trend['trend'] == 'stable_low':
                st.success(f"✅ **Air quality is STABLE and SAFE** (all values in LOW range)")
                st.write("- Minor fluctuations within safe zone (1-3)")
                st.write("- Outdoor activities are safe for general population")
            else:
                st.info(f"🟡 **Air quality is STABLE** (no significant change)")
            
            st.write(f"- **Peak AQHI**: {trend['max_aqhi']:.1f} (worst conditions)")
            st.write(f"- **Minimum AQHI**: {trend['min_aqhi']:.1f} (best conditions)")
            st.write(f"- **3-Day Average**: {trend['average_aqhi']:.1f}")
    
    elif st.session_state.raw_data:
        st.error("Could not fetch historical trend data")
    else:
        st.info("👈 Click 'Generate Daily Brief' to see trend analysis")

# Tab 4: AI Agents
with tab4:
    st.header("🤖 AI Agent Architecture")
    
    st.markdown("""
    This application uses **CrewAI** with 5 specialized AI agents working together to analyze environmental data 
    and generate comprehensive health briefings. Each agent has a specific role and expertise.
    """)
    
    st.divider()
    
    # Agent 1
    st.subheader("1. 📊 Data Integration Specialist")
    st.markdown("""
    **Role:** Environmental Data Integration Specialist
    
    **Responsibilities:**
    - Extracts and formats data from all provided sources
    - Structures information for downstream agents
    - Creates standardized data format (BRIEF_* tokens)
    - Ensures data accuracy and completeness
    
    **Input Sources:**
    - AQHI (Air Quality Health Index)
    - Individual Pollutants (PM2.5, O3, NO2)
    - 3-day historical trends
    - Weather conditions
    - Pollen data
    
    **Output:** Structured data summary with exact values for all metrics
    """)
    
    st.divider()
    
    # Agent 2
    st.subheader("2. 🫁 Pollutant Health Analyst")
    st.markdown("""
    **Role:** Pollutant Health Specialist
    
    **Expertise:**
    - **PM2.5:** Fine particulates, lung inflammation, cardiovascular stress
    - **O3 (Ozone):** Respiratory irritant, reduced lung function
    - **NO2 (Nitrogen Dioxide):** Airway inflammation, breathing difficulties
    
    **Responsibilities:**
    - Analyzes specific health impacts of each pollutant
    - Compares levels against WHO safety standards
    - Identifies dangerous pollutant combinations
    - Highlights vulnerable population risks
    
    **Output:** Pollutant-specific health impact analysis
    """)
    
    st.divider()
    
    # Agent 3
    st.subheader("3. 📈 Air Quality Trend Analyst")
    st.markdown("""
    **Role:** Air Quality Trend Analyst
    
    **Responsibilities:**
    - Analyzes 3-day AQHI historical patterns
    - Identifies trends (increasing, decreasing, stable_low)
    - Detects peak pollution times
    - Provides 24-hour forecasts
    - Issues early warnings for degrading conditions
    
    **Analysis Categories:**
    - **Increasing:** Air quality worsening
    - **Decreasing:** Air quality improving
    - **Stable_low:** Consistently safe conditions
    - **Stable:** No significant change
    
    **Output:** Trend analysis with context and forecasts
    """)
    
    st.divider()
    
    # Agent 4
    st.subheader("4. 🏥 Health Risk Stratification Specialist")
    st.markdown("""
    **Role:** Health Risk Stratification Specialist
    
    **Responsibilities:**
    - Creates evidence-based health recommendations
    - Tailors guidance to actual air quality levels
    - Provides population-specific advice
    - Recommends protective measures when warranted
    
    **Population Groups:**
    - **General Population:** Safe activity guidelines
    - **Children & Asthmatics:** Particulate and ozone sensitivity
    - **Elderly & Cardiovascular:** PM2.5 and NO2 concerns
    - **Pregnant Women:** Fetal development risks
    - **Outdoor Workers:** Cumulative exposure management
    
    **Risk Levels:**
    - AQHI 1-3: Excellent - No restrictions
    - AQHI 4-6: Moderate - Monitor sensitive groups
    - AQHI 7+: High - Protective measures required
    
    **Output:** Stratified, actionable health recommendations
    """)
    
    st.divider()
    
    # Agent 5
    st.subheader("5. 📝 Public Health Communications Specialist")
    st.markdown("""
    **Role:** Public Health Communications Specialist
    
    **Responsibilities:**
    - Formats data into clear, professional briefs
    - Uses exact values from Data Integration Agent
    - Creates structured markdown reports
    - Ensures scientific accuracy with readability
    - Synthesizes insights from all agents
    
    **Brief Structure:**
    1. Executive Summary (key findings at a glance)
    2. Current Air Quality & Pollutants (exact measurements)
    3. 3-Day Trend Analysis (historical context)
    4. Health Recommendations (by population group)
    5. Protective Measures (when needed)
    
    **Output:** Final daily environmental health brief
    """)
    
    st.divider()
    
    # Workflow
    st.subheader("🔄 Agent Workflow")
    
    col1, col2, col3 = st.columns([1, 0.1, 1])
    
    with col1:
        st.markdown("""
        **Sequential Processing:**
        1. **Data Integration** → Extracts all metrics
        2. **Pollutant Analysis** → Uses data from Agent 1
        3. **Trend Analysis** → Uses data from Agent 1
        4. **Risk Stratification** → Uses Agents 2 & 3
        5. **Communications** → Synthesizes all agents
        """)
    
    with col3:
        st.markdown("""
        **Data Flow:**
        ```
        API Sources
            ↓
        Agent 1: Integration
            ↓
        Agents 2 & 3: Analysis
            ↓
        Agent 4: Recommendations
            ↓
        Agent 5: Final Brief
            ↓
        User Display
        ```
        """)
    
    st.divider()
    
    # Technical Details
    st.subheader("⚙️ Technical Implementation")
    
    st.markdown("""
    **AI Model:** OpenAI GPT-4o-mini (via user's API key)
    
    **Framework:** CrewAI (Sequential Process)
    
    **Key Features:**
    - Context sharing between agents
    - No hallucination - agents use only provided data
    - Structured task dependencies
    - Real-time processing (2-3 minutes per brief)
    
    **Why Multiple Agents?**
    - **Specialization:** Each agent focuses on specific expertise
    - **Accuracy:** Structured data flow prevents errors
    - **Transparency:** Clear chain of analysis
    - **Quality:** Multiple perspectives ensure comprehensive output
    """)

# Tab 5: Logs
with tab5:
    st.header("Agent Activity Logs")
    
    if st.session_state.logs:
        st.code(st.session_state.logs, language="text")
        
        st.download_button(
            label="📥 Download Logs",
            data=st.session_state.logs,
            file_name="agent_logs.txt",
            mime="text/plain"
        )
    else:
        st.info("Logs will appear here after generating the brief")

# --- Footer ---
st.divider()
st.markdown("""
---
**Technical Implementation:**
- ✅ Multi-source API Integration (5 real-time data sources)
- ✅ Individual Pollutant Analysis (PM2.5, O3, NO2)
- ✅ 3-Day Historical Trends with Visualization
- ✅ CrewAI with 5 Specialized Agents
- ✅ Data Synthesis & Health Risk Analysis
- ✅ Bring Your Own Key (BYOK) Support

**Data Freshness:** All data fetched in real-time
""")