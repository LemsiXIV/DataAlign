# DataAlign v2.0 - GPT-4 Integration

## 🚀 Overview

DataAlign now includes GPT-4 powered intelligent data processing to enhance file comparison accuracy and handle messy data formats automatically.

## 🤖 GPT-4 Features

### Intelligent Data Analysis
- **Data Structure Detection**: Automatically identifies data types, patterns, and inconsistencies
- **Format Standardization**: Normalizes different date formats, currency values, and text casing
- **Column Mapping**: Suggests optimal column relationships for comparison

### Smart Data Cleaning
- **Automatic Formatting**: Fixes inconsistent data formats (dates, numbers, text)
- **Duplicate Detection**: Identifies and handles duplicate entries intelligently  
- **Missing Value Management**: Smart handling of null, empty, and placeholder values

### Enhanced Comparison
- **Semantic Matching**: Uses AI to match similar but differently formatted data
- **Confidence Scoring**: Provides accuracy metrics for comparison results
- **Optimization Suggestions**: Recommends improvements for better data alignment

## 📋 Setup Instructions

### 1. Install Dependencies
```bash
python setup_gpt.py
```
This will install the OpenAI package and set up configuration files.

### 2. Configure API Key
Edit the `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=your_openai_api_key_here
ENABLE_GPT_PROCESSING=true
```

### 3. Start the Application
```bash
python start.py
```

## 🎯 Usage

### Fast Test with GPT Enhancement
1. Go to the homepage and click "Fast Test"
2. Upload your two files (CSV, XLSX, JSON)
3. Check the "🤖 Amélioration GPT-4 (Expérimental)" option
4. Click "Compaire" to start enhanced comparison

### API Endpoints

The GPT integration adds the following API endpoints:

#### Analyze File Structure
```bash
POST /gpt/analyze-file
Content-Type: multipart/form-data

# Upload file for AI analysis
```

#### Get Column Suggestions  
```bash
POST /gpt/suggest-comparison
Content-Type: application/json

{
  "columns1": ["name", "amount", "date"],
  "columns2": ["customer_name", "value", "timestamp"]
}
```

#### Apply Data Cleaning
```bash
POST /gpt/apply-cleaning
Content-Type: application/json

{
  "data": [...],
  "cleaning_instructions": "normalize dates and currency"
}
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `ENABLE_GPT_PROCESSING`: Enable/disable GPT features (default: true)

### GPT Processor Settings
```python
# In app/services/gpt_data_processor.py
class GPTDataProcessor:
    def __init__(self):
        self.model = "gpt-4"  # Can be changed to gpt-3.5-turbo for cost savings
        self.max_tokens = 1000
        self.temperature = 0.1  # Low temperature for consistent results
```

## 📊 Performance Considerations

### Token Usage
- **Small files** (<100 rows): ~200-500 tokens per analysis
- **Medium files** (100-1000 rows): ~500-1500 tokens per analysis  
- **Large files** (>1000 rows): Processed in chunks to optimize costs

### Cost Estimation
- GPT-4: ~$0.03 per 1K tokens
- GPT-3.5-Turbo: ~$0.002 per 1K tokens
- Average cost per file analysis: $0.01-$0.05

### Optimization Tips
1. **Use chunk processing** for large files
2. **Cache results** to avoid re-analysis
3. **Pre-filter** data to reduce token usage
4. **Use GPT-3.5-turbo** for cost-sensitive applications

## 🛠️ Technical Implementation

### Architecture
```
DataAlign App
├── GPT Data Processor Service
│   ├── analyze_data_structure()
│   ├── clean_data_chunk()
│   └── suggest_comparison_columns()
├── GPT Routes Blueprint
│   ├── /analyze-file
│   ├── /suggest-comparison
│   └── /apply-cleaning
└── Enhanced File Processing
    ├── Fast Upload with GPT
    └── Standard Comparison with AI
```

### Integration Points
1. **File Upload**: GPT processing option in upload forms
2. **Data Reading**: Enhanced with automatic cleaning
3. **Comparison**: Improved accuracy with semantic matching
4. **Results**: AI-generated suggestions and optimizations

## 🧪 Testing

### Run Integration Tests
```bash
python test_gpt_integration.py
```

### Test API Endpoints
```bash
# Test file analysis
curl -X POST http://localhost:5000/gpt/analyze-file \
  -F "file=@sample.csv"

# Test column suggestions
curl -X POST http://localhost:5000/gpt/suggest-comparison \
  -H "Content-Type: application/json" \
  -d '{"columns1": ["name"], "columns2": ["customer_name"]}'
```

## 🔒 Security & Privacy

### Data Privacy
- **No data storage**: OpenAI does not store data sent via API (as of API policy)
- **Local processing**: Sensitive data can be processed locally first
- **Encryption**: All API calls use HTTPS encryption

### Best Practices
1. **Review data** before sending to OpenAI API
2. **Use environment variables** for API keys
3. **Implement rate limiting** for production use
4. **Monitor API usage** and costs

## 🐛 Troubleshooting

### Common Issues

#### GPT Processing Not Available
```
⚠️ GPT-4 non configuré - traitement standard appliqué
```
**Solution**: Check that `OPENAI_API_KEY` is set in your `.env` file

#### API Rate Limit Exceeded
```
❌ Erreur GPT-4: Rate limit exceeded
```
**Solution**: Implement exponential backoff or reduce request frequency

#### Invalid API Key
```
❌ Erreur GPT-4: Invalid API key
```
**Solution**: Verify your OpenAI API key is correct and has sufficient credits

### Debug Mode
Enable debug logging to see detailed GPT processing information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Future Enhancements

### Planned Features
- **Custom AI Models**: Support for local AI models (Ollama, LLaMA)
- **Advanced Analytics**: AI-powered data insights and recommendations
- **Automated Workflows**: Smart scheduling and processing automation
- **Multi-language Support**: Enhanced international data handling

### Community Contributions
We welcome contributions to improve the GPT integration:
1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Submit a pull request

## 📞 Support

For issues related to GPT integration:
1. Check this README for common solutions
2. Review the troubleshooting section
3. Check application logs for detailed error messages
4. Create an issue with reproduction steps

---

**DataAlign v2.0** - Intelligent File Comparison with GPT-4 Enhancement 🚀
