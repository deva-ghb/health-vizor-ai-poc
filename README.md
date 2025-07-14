# HealthVizor - AI-Powered Health Analysis Tool

HealthVizor is an AI assistant that analyzes user lifestyle and health data to deliver actionable, science-backed insights and personalized recommendations for optimizing health and well-being.

## Features

- **Multi-Model Support**: Compare results from different LLM models (GPT-4.1, Gemini, O4, O3, etc.)
- **Comprehensive Health Data Analysis**: 
  - User onboarding conversations
  - Personal details and demographics
  - Biomarkers and lab data
  - Health category scores
  - Existing recommendations
- **Structured Output**: Get organized insights with analysis summaries, key insights, and actionable recommendations
- **Evidence-Based Recommendations**: Science-backed supplement, lifestyle, and nutrition advice
- **Export Functionality**: Download results as Excel files for further analysis

## Recent Updates

### Enhanced Prompt Integration
- **Centralized Prompt Management**: All prompts are now managed in `prompt.py` for easy maintenance
- **New Data Fields**: Added support for biomarkers data and category scores
- **Improved Error Handling**: Better JSON parsing and fallback responses
- **Consistent Disclaimer**: Always includes medical disclaimer

### New Input Fields
- **Biomarkers Data**: Enter lab results, health metrics, and biomarker information
- **Category Scores**: Input HealthVizor category scores and health assessments
- **Enhanced User Interface**: Better organized input sections with helpful tooltips

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd health_vizor
```

2. Install dependencies:
```bash
pip install streamlit openai pydantic pandas litellm xlsxwriter
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export GEMINI_API_KEY="your-gemini-api-key"  # Optional, for Gemini models
```

## Usage

1. Run the Streamlit application:
```bash
streamlit run health_vizor.py
```

2. Fill in the required information:
   - **User Details**: Name, age, gender, height, weight, and health goals
   - **User Conversation**: Paste onboarding Q&A or health-related conversations
   - **Biomarkers Data**: Enter lab results, health metrics, or biomarker information
   - **Category Scores**: Input HealthVizor category scores and health assessments
   - **Recommendations**: Add any existing recommendations or requirements

3. Select models and generate reports:
   - Choose from available LLM models (GPT-4.1, Gemini, O4, O3, etc.)
   - Generate individual reports or compare multiple models
   - Export results to Excel for further analysis

## File Structure

```
health_vizor/
├── health_vizor.py      # Main Streamlit application
├── prompt.py           # Centralized prompt template
├── llm_utils.py        # LLM calling utilities
├── test_integration.py # Integration test script
├── LLM_call.ipynb      # Jupyter notebook for testing
└── README.md           # This file
```

## Model Support

The application supports multiple LLM providers:

### OpenAI Models
- GPT-4.1
- GPT-4.1 Mini
- GPT-4.1 Nano

### Anthropic Models
- O4 Mini
- O3 Mini
- O3

### Google Models
- Gemini 1.5 Pro Latest
- Gemini 2.0 Flash
- Gemini 2.0 Flash Exp
- Gemini 2.0 Flash Lite Preview

## Output Format

The application generates structured responses with:

- **Analysis Summary**: Concise overview of key health trends (max 100 words)
- **Key Insights**: 1-3 evidence-based insights with scientific references
- **Actionable Recommendations**:
  - **Supplements**: Up to 2 evidence-based supplement recommendations
  - **Lifestyle**: Up to 2 practical lifestyle changes
  - **Nutrition**: Up to 2 dietary recommendations
- **Disclaimer**: Medical disclaimer for educational purposes

## Testing

Run the integration test to verify prompt functionality:

```bash
python test_integration.py
```

## Important Notes

- **Medical Disclaimer**: All recommendations are for educational purposes only and do not constitute medical advice
- **Healthcare Provider Consultation**: Always encourage users to consult healthcare providers before starting new regimens
- **Data Privacy**: Ensure proper handling of sensitive health information
- **API Keys**: Keep API keys secure and never commit them to version control

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Support

For questions or issues, please [create an issue](link-to-issues) or contact the development team. 