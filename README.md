# 🌳 Ottawa Environmental Health Monitor

Advanced multi-source environmental health intelligence with real-time pollutant analysis and 3-day air quality trends for Ottawa.

## Features

- ✅ **Multi-source API Integration** - 5 real-time data sources
- ✅ **Individual Pollutant Analysis** - PM2.5, O3, NO2 tracking
- ✅ **3-Day Historical Trends** - Visual trend analysis
- ✅ **CrewAI Intelligence** - 5 specialized AI agents
- ✅ **Health Risk Analysis** - Population-specific recommendations
- ✅ **BYOK Support** - Bring Your Own OpenAI API Key

## Data Sources

- **AQHI**: Environment Canada
- **Pollutants**: Air Quality Ontario
- **Weather**: Open-Meteo API
- **Trends**: 3-day historical AQHI data
- **Pollen**: Seasonal data

## Prerequisites

- Python 3.8+
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

## Local Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ottawa-environmental-health-monitor
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
streamlit run app.py
```

4. **Enter your OpenAI API key** in the sidebar when the app opens

## Files Structure

```
├── app.py              # Main Streamlit application
├── agents.py           # CrewAI agents and tasks
├── tools.py            # API integration functions
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Important Notes

### Security
- ⚠️ **Never commit your API key** to GitHub
- The app uses BYOK (Bring Your Own Key) - users enter their own OpenAI API key
- API keys are not stored or persisted

### API Keys
- Users need their own OpenAI API key
- Get one at: https://platform.openai.com/api-keys
- Free tier available with limited credits

### Streamlit Cloud Free Tier Limits
- 1 GB RAM
- 1 CPU core
- Public apps only
- Community support

## Troubleshooting

### "Module not found" error
- Ensure `requirements.txt` has all dependencies
- Redeploy from Streamlit Cloud dashboard

### API key issues
- Make sure you're using a valid OpenAI API key
- Check your OpenAI account has available credits

### Data not loading
- Check API endpoints are accessible
- Verify internet connection
- Some APIs may have rate limits

## Architecture

### AI Agents (CrewAI)
1. **Data Integration Specialist** - Extracts and formats environmental data
2. **Pollutant Health Analyst** - Analyzes specific pollutant impacts
3. **Trend Analyst** - Evaluates 3-day AQHI trends
4. **Risk Stratification Specialist** - Creates tailored health recommendations
5. **Communications Specialist** - Formats final daily brief

### Data Flow
```
API Sources → app.py (fetch data) → CrewAI Agents (analyze) → Daily Brief
```

## Contributing

Feel free to submit issues or pull requests!

## License

MIT License - Feel free to use and modify

---

**Built with:** Streamlit, CrewAI, LangChain, OpenAI GPT-4o-mini