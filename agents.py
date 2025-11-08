import os
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# ============================================================
# CREW CREATION FUNCTION
# ============================================================

def create_crew(api_key: str):
    """
    Creates a Crew with multi-pollutant and trend analysis.
    
    Args:
        api_key: OpenAI API key provided by the user
    
    Returns:
        Crew instance configured with the provided API key
    """
    
    # Create LLM instance with user's API key
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=api_key
    )
    
    # ============================================================
    # AGENTS
    # ============================================================
    
    data_integration_agent = Agent(
        role="Environmental Data Integration Specialist",
        goal="Collect and integrate real-time pollutant data (PM2.5, O3, NO2) with AQHI and historical trends",
        backstory=(
            "You are an expert environmental data scientist specializing in air quality metrics. "
            "You fetch and synthesize data from multiple sources: AQHI, individual pollutants (PM2.5, O3, NO2), "
            "3-day historical trends, weather, and pollen. You understand how pollutants interact."
        ),
        llm=llm,
        verbose=True
    )
    
    pollutant_health_analyst = Agent(
        role="Pollutant Health Specialist",
        goal="Analyze specific health impacts of individual pollutants and their combined effects",
        backstory=(
            "You are a respiratory epidemiologist who specializes in specific pollutant health impacts:\n"
            "- PM2.5: Fine particulates, lung inflammation, cardiovascular stress\n"
            "- O3 (Ozone): Respiratory irritant, reduces lung function\n"
            "- NO2: Nitrogen dioxide, airway inflammation\n"
            "You provide pollutant-specific health guidance and identify dangerous combinations."
        ),
        llm=llm,
        verbose=True
    )
    
    trend_analyst = Agent(
        role="Air Quality Trend Analyst",
        goal="Analyze AQHI historical trends and predict future air quality patterns",
        backstory=(
            "You are a data analyst specializing in air quality trends. "
            "You analyze 3-day historical AQHI data to identify:\n"
            "- Increasing vs decreasing trends\n"
            "- Peak pollution times\n"
            "- Expected pollution trajectory\n"
            "- Early warnings for degrading air quality"
        ),
        llm=llm,
        verbose=True
    )
    
    risk_stratification_agent = Agent(
        role="Health Risk Stratification Specialist",
        goal="Create accurate, evidence-based health recommendations that match actual air quality conditions",
        backstory=(
            "You are a public health strategist who provides balanced, accurate guidance. "
            "You NEVER exaggerate risks when air quality is good. When AQHI is 1-3 and pollutants "
            "are low, you clearly state that conditions are excellent and safe for everyone. "
            "You only recommend restrictions when data actually warrants concern. "
            "You understand that unnecessary warnings reduce public trust and compliance."
        ),
        llm=llm,
        verbose=True
    )
    
    communications_specialist = Agent(
        role="Public Health Communications Specialist",
        goal="Create clear, scientifically rigorous daily health briefs with pollutant breakdowns",
        backstory=(
            "You are a science communicator who excels at presenting complex multi-pollutant data. "
            "You create professional briefs that include:\n"
            "- AQHI overview\n"
            "- Individual pollutant levels and health risks\n"
            "- 3-day trend analysis and forecasts\n"
            "- Pollutant-specific health recommendations"
        ),
        llm=llm,
        verbose=True
    )
    
    # ============================================================
    # TASKS
    # ============================================================
    
    task_1_integrate_data = Task(
        description=(
            "You have been provided with pre-fetched air quality data for Ottawa in the inputs.\n"
            "DO NOT call any tools - the data is already available in:\n"
            "- {aqhi_data}\n"
            "- {pollutants_data}\n"
            "- {trend_data}\n"
            "- {weather_data}\n"
            "- {pollen_data}\n"
            "\n"
            "Extract and format the data in BRIEF_* format for task_5 to use:\n"
            "\n"
            "BRIEF_AQHI_VALUE:[from aqhi_data['aqhi_value']]\n"
            "BRIEF_AQHI_RISK:[from aqhi_data['risk_level']]\n"
            "BRIEF_TIMESTAMP:[from aqhi_data['timestamp']]\n"
            "BRIEF_PM25:[from pollutants_data['pm25']]\n"
            "BRIEF_O3:[from pollutants_data['o3']]\n"
            "BRIEF_NO2:[from pollutants_data['no2']]\n"
            "BRIEF_TEMPERATURE:[from weather_data['temperature_celsius']]\n"
            "BRIEF_HUMIDITY:[from weather_data['relative_humidity']]\n"
            "BRIEF_TREND:[from trend_data['trend']]\n"
            "BRIEF_CHANGE_PERCENT:[from trend_data['change_percent']]\n"
            "BRIEF_PEAK_AQHI:[from trend_data['max_aqhi']]\n"
            "\n"
            "Then provide analysis of these values."
        ),
        expected_output=(
            "Data values in BRIEF_* format extracted from the provided inputs, "
            "followed by analysis. Use exact values from the input data."
        ),
        agent=data_integration_agent,
    )
    
    task_2_analyze_pollutants = Task(
        description=(
            "Read the STRUCTURED DATA SUMMARY from task_1 above.\n"
            "\n"
            "⚠️ CRITICAL: Quote the EXACT values from that summary. Do NOT estimate or hallucinate.\n"
            "\n"
            "Example (if summary shows PM2.5: 4.0 µg/m³):\n"
            "State: 'The integrated data shows PM2.5: 4.0 µg/m³'\n"
            "Do NOT say: 'PM2.5 is 27 µg/m³' or any other value\n"
            "\n"
            "Analyze using ONLY the values from the task_1 summary:\n"
            "\n"
            "PM2.5:\n"
            "- Report exact value from summary vs WHO safe level (12 µg/m³)\n"
            "- Health implications at that specific level\n"
            "\n"
            "O3 (Ozone):\n"
            "- Report exact value from summary\n"
            "- Respiratory implications\n"
            "\n"
            "NO2:\n"
            "- Report exact value from summary\n"
            "- Airway impacts\n"
            "\n"
            "Vulnerable populations for these specific values."
        ),
        expected_output=(
            "Pollutant analysis using EXACT values quoted from data summary. "
            "No made-up numbers. Cross-references task_1 data."
        ),
        agent=pollutant_health_analyst,
        context=[task_1_integrate_data]
    )
    
    task_3_analyze_trends = Task(
        description=(
            "Use the TREND DATA from the task_1 STRUCTURED DATA SUMMARY.\n"
            "\n"
            "⚠️ CRITICAL: Quote exact trend values from summary. Do NOT hallucinate historical data.\n"
            "\n"
            "From task_1 summary, reference:\n"
            "- Trend: [exact from summary]\n"
            "- Change %: [exact from summary]\n"
            "- Peak AQHI: [exact from summary]\n"
            "\n"
            "Provide analysis:\n"
            "1. What does the trend mean? (stable_low, increasing, decreasing)\n"
            "2. Is this movement concerning? (only if crossing risk zones)\n"
            "3. Peak pollution times\n"
            "4. 24-hour forecast based on trend\n"
            "5. Context: If all values in LOW zone, emphasize stability not concern\n"
            "\n"
            "Example (if trend summary shows stable_low):\n"
            "State: 'The data shows stable_low trend with peak AQHI of 2.3'\n"
            "Do NOT say: 'AQHI is worsening' or '40% increase'"
        ),
        expected_output=(
            "Trend analysis using exact values from data summary. "
            "Contextual interpretation. No hallucinated historical data."
        ),
        agent=trend_analyst,
        context=[task_1_integrate_data]
    )
    
    task_4_health_recommendations = Task(
        description=(
            f"Create detailed health recommendations for {datetime.now().strftime('%B %d, %Y')}.\n"
            "\n"
            "⚠️ CRITICAL: Tailor recommendations to ACTUAL air quality levels:\n"
            "\n"
            "IF AQHI 1-3 AND PM2.5 < 12 µg/m³ (EXCELLENT/LOW RISK):\n"
            "- State clearly: 'Air quality is EXCELLENT - safe for ALL populations'\n"
            "- General population: No restrictions, all outdoor activities safe\n"
            "- At-risk populations: Normal activities permitted, standard precautions only\n"
            "- Do NOT recommend limiting outdoor time or avoiding activities\n"
            "- Do NOT suggest masks unless specifically requested\n"
            "- Emphasize this is ideal air quality\n"
            "\n"
            "IF AQHI 4-6 OR PM2.5 12-35 µg/m³ (MODERATE):\n"
            "- General population: Normal activities, monitor sensitive individuals\n"
            "- At-risk populations: Consider reducing prolonged or heavy exertion\n"
            "\n"
            "IF AQHI 7+ OR PM2.5 > 35 µg/m³ (HIGH/VERY HIGH):\n"
            "- General population: Reduce outdoor exertion\n"
            "- At-risk populations: Avoid outdoor activities, use masks (N95/P100)\n"
            "- Indoor air purifiers recommended\n"
            "\n"
            "Structure recommendations:\n"
            "1. Overall Air Quality Assessment (be positive if conditions are good!)\n"
            "2. General Population Guidance\n"
            "3. At-Risk Populations (only add restrictions if needed)\n"
            "4. Specific Mitigation Measures (only if air quality warrants it)\n"
            "\n"
            "Use the trend analysis: if improving or stable_low, emphasize safety."
        ),
        expected_output=(
            "Accurate health recommendations that match the actual air quality level. "
            "Positive messaging for good air quality. Restrictions only when warranted."
        ),
        agent=risk_stratification_agent,
        context=[task_2_analyze_pollutants, task_3_analyze_trends]
    )
    
    task_5_write_brief = Task(
        description=(
            "TASK: Format the brief using exact values from task_1 output.\n"
            "DO NOT regenerate or interpret - just insert the values.\n"
            "\n"
            "Extract from task_1 output:\n"
            "BRIEF_AQHI_VALUE: [copy exactly]\n"
            "BRIEF_AQHI_RISK: [copy exactly]\n"
            "BRIEF_TIMESTAMP: [copy exactly]\n"
            "BRIEF_PM25: [copy exactly]\n"
            "BRIEF_O3: [copy exactly]\n"
            "BRIEF_NO2: [copy exactly]\n"
            "BRIEF_TEMPERATURE: [copy exactly]\n"
            "BRIEF_TREND: [copy exactly]\n"
            "BRIEF_CHANGE_PERCENT: [copy exactly]\n"
            "BRIEF_PEAK_AQHI: [copy exactly]\n"
            "\n"
            "Format into markdown brief:\n"
            "\n"
            "## Daily Environmental Health Brief\n"
            "\n"
            "**Executive Summary:** According to real-time data from [BRIEF_TIMESTAMP], "
            "AQHI is [BRIEF_AQHI_VALUE] ([BRIEF_AQHI_RISK] risk) with PM2.5 at [BRIEF_PM25] µg/m³.\n"
            "\n"
            "### 1. Current Air Quality & Pollutants\n"
            "- **AQHI:** [BRIEF_AQHI_VALUE] ([BRIEF_AQHI_RISK])\n"
            "- **PM2.5:** [BRIEF_PM25] µg/m³ (WHO safe level: 12 µg/m³)\n"
            "- **Ozone (O3):** [BRIEF_O3] ppb\n"
            "- **Nitrogen Dioxide (NO2):** [BRIEF_NO2] ppb\n"
            "- **Data Source:** Environment Canada, Air Quality Ontario\n"
            "- **Timestamp:** [BRIEF_TIMESTAMP]\n"
            "\n"
            "### 2. 3-Day Trend\n"
            "- **Trend:** [BRIEF_TREND]\n"
            "- **Change:** [BRIEF_CHANGE_PERCENT]%\n"
            "- **Peak AQHI:** [BRIEF_PEAK_AQHI]\n"
            "- **Temperature:** [BRIEF_TEMPERATURE]°C\n"
            "\n"
            "Then use task_2, task_3, task_4 analysis for health recommendations.\n"
            "\n"
            "CRITICAL: Every [BRIEF_*] value must be copied EXACTLY from task_1."
        ),
        expected_output=(
            "Markdown brief with all values directly from task_1 BRIEF_* tokens. "
            "No interpretation. No regeneration. Pure template insertion."
        ),
        agent=communications_specialist,
        context=[task_1_integrate_data, task_2_analyze_pollutants, task_3_analyze_trends, task_4_health_recommendations]
    )
    
    # ============================================================
    # CREATE AND RETURN CREW
    # ============================================================
    
    return Crew(
        agents=[
            data_integration_agent,
            pollutant_health_analyst,
            trend_analyst,
            risk_stratification_agent,
            communications_specialist
        ],
        tasks=[
            task_1_integrate_data,
            task_2_analyze_pollutants,
            task_3_analyze_trends,
            task_4_health_recommendations,
            task_5_write_brief
        ],
        process=Process.sequential,
        verbose=True
    )