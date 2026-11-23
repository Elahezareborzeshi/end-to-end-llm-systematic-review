# LLM-Powered Systematic Review Framework: Comprehensive Documentation Instructions

## OVERVIEW
You are tasked with writing documentation for a sophisticated, end-to-end LLM-powered systematic review framework developed by Elahe Zare Borzeshi. This framework automates and assists researchers in conducting systematic reviews using large language models (LLMs) and AI technologies. The framework is implemented as a Streamlit web application with Python backend.

## TECHNICAL ARCHITECTURE

### Core Technology Stack
- **Frontend**: Streamlit web interface with custom CSS styling
- **Backend**: Python with modular architecture
- **LLM Integration**: OpenAI GPT-4/GPT-4o models via OpenAI API
- **Vector Database**: FAISS for semantic search and RAG functionality
- **Text Processing**: LangChain for LLM orchestration and retrieval-augmented generation
- **Data Sources**: PubMed/NCBI APIs for medical literature access
- **Libraries**: BioPython, BeautifulSoup, Requests, PyPDF2, Metapub
- **Configuration**: Environment-based configuration with .env files

### System Requirements
```
Python 3.8+
Required APIs: OpenAI API, PubMed API
Dependencies: See requirements.txt (17 key packages including openai==1.43.0, streamlit==1.38.0, langchain-openai==0.1.23)
```

## COMPLETE WORKFLOW PIPELINE

The framework implements a 10-step systematic review pipeline:

### 1. Research Question Formulation
- **AI-Powered Question Generator**: Uses GPT-4o to suggest research questions based on partial input
- **Template System**: Provides 10+ research question templates for different study types
- **Adaptive Learning**: Learns from user feedback to improve future suggestions
- **PICO Format Support**: Guides users toward Population, Intervention, Comparison, Outcome format
- **Real-time Suggestions**: Tab completion-style suggestions as users type

### 2. Selection Criteria Definition
- **Inclusion Criteria Assistant**: AI generates criteria based on research question context
- **Exclusion Criteria Assistant**: Complementary exclusion criteria generation
- **Template Library**: Pre-built criteria templates for common study types
- **Interactive Refinement**: Users can iterate and refine criteria with AI assistance
- **Feedback Learning**: System learns from user preferences to improve suggestions

### 3. Keyword Extraction and Enhancement
- **LLM-Based Extraction**: Uses GPT-4o to extract relevant keywords from research questions
- **Medical Terminology Focus**: Specialized prompts for scientific and medical synonyms
- **Multi-Temperature Generation**: Uses different temperature settings for diverse keyword generation
- **Deduplication**: Automatic removal of duplicate keywords
- **Manual Editing**: Users can add, remove, or modify extracted keywords

### 4. MeSH Term Discovery and Validation
- **NCBI MeSH API Integration**: Automated MeSH term lookup via PubMed APIs
- **Hierarchical Term Extraction**: Retrieves main terms, entry terms, and previous indexing terms
- **RAG-Based Relevance Assessment**: Uses vector similarity to assess term relevance to research question
- **Interactive Selection Interface**: Checkbox-based term selection with grouping by keywords
- **Duplicate Prevention**: Automatic detection and removal of duplicate MeSH terms

### 5. Boolean Search Query Construction
- **Automated Query Building**: Constructs complex Boolean queries with proper operators
- **Field Tag Integration**: Combines MeSH terms and Title/Abstract searches appropriately
- **Query Validation System**: Comprehensive validation with 15+ validation rules including:
  - Parentheses balance checking
  - Boolean operator syntax validation
  - Field tag verification
  - Quote balance verification
  - PubMed-specific syntax checking
- **Auto-Fix Functionality**: Automatically corrects common query construction errors
- **Query Formatting**: Pretty-prints complex queries for readability

### 6. Literature Download and Management
- **PubMed Integration**: Downloads articles using BioPython and Entrez APIs
- **Batch Processing**: Handles large-scale downloads with pagination
- **Error Handling**: Robust retry mechanisms for network failures
- **Metadata Extraction**: Extracts title, abstract, authors, journal, publication date, PMID
- **File Management**: Organizes downloaded articles in structured JSON format
- **Progress Tracking**: Real-time progress indicators for download operations

### 7. Article Deduplication
- **Intelligent Duplicate Detection**: Uses article IDs for accurate deduplication
- **Multiple ID Comparison**: Compares DOI, PMID, and other identifiers
- **Safe Removal**: Moves duplicates to separate folder rather than deletion
- **Statistics Reporting**: Provides counts of removed duplicates

### 8. Title/Abstract Screening
- **Dual Mode Operation**: Manual and automated screening modes
- **RAG-Based AI Screening**: Uses vector similarity and LLM reasoning for automated decisions
- **Interactive Interface**: Clean UI with Include/Exclude buttons and keyboard shortcuts
- **Decision Tracking**: Records all screening decisions with timestamps and reasoning
- **Accuracy Monitoring**: Tracks AI prediction accuracy against human decisions
- **Feedback Integration**: User corrections improve future AI screening performance
- **Progress Visualization**: Real-time progress tracking and statistics

### 9. Full Text Download and Screening
- **Comprehensive Full Text Retrieval**: Downloads full PDFs where available
- **Advanced RAG Screening**: Uses full article content for more accurate screening decisions
- **Criteria-Based Assessment**: Incorporates inclusion/exclusion criteria in screening logic
- **Content Truncation**: Handles large documents with intelligent truncation
- **Quality Assessment**: Evaluates methodological quality and relevance
- **Multi-Factor Decision Making**: Considers methodology, population, outcomes, and data availability

### 10. Data Extraction and Synthesis
- **AI-Powered Extraction**: Uses LLM to extract specific data fields from included articles
- **Customizable Templates**: User-defined extraction instructions and field specifications
- **Structured Output**: Generates JSON-formatted extracted data for each article
- **Fallback Handling**: Uses abstracts when full text is unavailable
- **Quality Indicators**: Marks whether extraction used full text or abstract only
- **Export Functionality**: Generates CSV output for analysis and meta-analysis

## ADVANCED AI FEATURES

### Retrieval-Augmented Generation (RAG) System
- **Vector Store Management**: FAISS-based vector storage for research context
- **Semantic Search**: Finds relevant previous decisions and examples
- **Context-Aware Reasoning**: Incorporates research question and criteria in all decisions
- **Memory Integration**: Builds knowledge base from user interactions
- **Adaptive Learning**: Improves performance based on user feedback patterns

### Intelligent Suggestion Engine
- **Multi-Template System**: 10+ templates each for research questions, data extraction, and criteria
- **Feedback Analysis**: Analyzes user preferences from historical interactions
- **Pattern Recognition**: Identifies successful suggestion patterns and styles
- **Adaptive Prompting**: Customizes AI prompts based on learned preferences
- **Continuous Learning**: Updates suggestions based on user acceptance/rejection patterns

### Quality Assurance Features
- **Validation Pipeline**: Multi-step validation for all user inputs
- **Error Prevention**: Proactive error detection and correction suggestions
- **Consistency Checking**: Ensures alignment between research question, criteria, and extraction
- **Progress Safeguards**: Prevents progression with invalid or incomplete steps

## USER INTERFACE DESIGN

### Streamlit Web Application
- **Responsive Design**: Clean, professional interface optimized for research workflows
- **Step-by-Step Navigation**: Clear progression through systematic review stages
- **Interactive Components**: Expandable sections, progress bars, real-time updates
- **Visual Feedback**: Color-coded status indicators, emoji-enhanced sections
- **Accessibility Features**: Keyboard shortcuts, clear labeling, help text

### Session Management
- **Persistent State**: Maintains progress across browser sessions
- **Auto-Save**: Automatic saving of all user inputs and decisions
- **Recovery Features**: Robust error recovery and state restoration
- **Export Options**: Multiple export formats for results and progress

## DATA MANAGEMENT AND SECURITY

### File Organization
```
data/
├── downloaded_articles/        # Original article JSON files
├── sample/                    # Example article data
├── user_feedback.jsonl       # Feedback for ML improvement
└── vector_store.txt          # RAG knowledge base
```

### API Security
- **Environment Variables**: Secure API key management via .env files
- **Rate Limiting**: Respectful API usage with built-in delays
- **Error Handling**: Graceful handling of API failures and limits

## CUSTOMIZATION AND EXTENSIBILITY

### Modular Architecture
- **Component Separation**: Clear separation of concerns across modules
- **Plugin System**: Easy addition of new data sources or AI models
- **Template System**: Extensible template library for different research domains
- **Configuration Management**: Centralized configuration for easy customization

### Research Domain Adaptation
- **Medical Research Focus**: Optimized for biomedical systematic reviews
- **MeSH Integration**: Deep integration with medical subject headings
- **Clinical Trial Support**: Specialized handling for clinical research methodologies
- **Meta-Analysis Preparation**: Data extraction optimized for meta-analysis requirements

## PERFORMANCE AND SCALABILITY

### Optimization Features
- **Batch Processing**: Efficient handling of large article collections
- **Caching**: Intelligent caching of API responses and AI generations
- **Parallel Processing**: Concurrent operations where appropriate
- **Memory Management**: Efficient handling of large document collections

### Error Handling and Recovery
- **Comprehensive Logging**: Detailed logging for troubleshooting
- **Graceful Degradation**: Continues operation despite partial failures
- **User Feedback**: Clear error messages and recovery suggestions
- **Backup Systems**: Multiple fallback options for critical operations

## VALIDATION AND QUALITY CONTROL

### Multi-Level Validation
1. **Input Validation**: Real-time validation of user inputs
2. **Query Validation**: 15+ validation rules for search queries
3. **Data Validation**: Ensures data integrity throughout pipeline
4. **Output Validation**: Verifies extraction completeness and accuracy

### Quality Metrics
- **Screening Accuracy**: AI vs. human decision agreement tracking
- **Completion Rates**: Progress tracking and completion statistics
- **Error Rates**: Monitoring and reporting of system errors
- **User Satisfaction**: Feedback collection and analysis

## INTEGRATION CAPABILITIES

### External APIs
- **PubMed/NCBI**: Primary literature source with comprehensive API integration
- **OpenAI**: GPT-4/GPT-4o for natural language processing tasks
- **Future Extensions**: Architecture supports additional databases and AI models

### Export and Interoperability
- **Standard Formats**: CSV, JSON export for external analysis tools
- **Meta-Analysis Ready**: Output formatted for RevMan, R, Stata
- **Citation Management**: Compatible with Zotero, Mendeley integration potential
- **Reporting Standards**: Supports PRISMA reporting requirements

## LEARNING AND ADAPTATION

### Machine Learning Components
- **User Preference Learning**: Adapts to individual researcher preferences
- **Domain Adaptation**: Learns domain-specific patterns and terminology
- **Quality Improvement**: Continuous improvement through feedback loops
- **Pattern Recognition**: Identifies successful research methodologies and approaches

## DEVELOPMENT AND DEPLOYMENT

### Development Environment
- **Python 3.8+**: Modern Python with type hints and async support
- **Virtual Environment**: Isolated dependency management
- **Version Control**: Git-based development workflow
- **Testing**: Comprehensive error handling and validation

### Deployment Options
- **Local Installation**: Single-researcher deployment
- **Team Deployment**: Multi-user institutional deployment
- **Cloud Options**: Scalable cloud deployment potential
- **Container Support**: Docker containerization ready

## FRAMEWORK BENEFITS AND INNOVATIONS

### Research Efficiency
- **Time Reduction**: 80%+ time savings compared to manual systematic reviews
- **Consistency**: Standardized methodology across all review stages
- **Reproducibility**: Detailed logging and transparent decision-making
- **Quality**: AI-assisted quality control and validation

### Methodological Advances
- **AI-Human Collaboration**: Optimal balance of automation and human expertise
- **Adaptive Learning**: Continuously improving performance
- **Comprehensive Coverage**: End-to-end systematic review support
- **Evidence-Based**: Built on systematic review best practices and standards

## FUTURE DEVELOPMENT

### Planned Enhancements
- **Multi-Database Support**: Expansion beyond PubMed to other literature databases
- **Advanced Analytics**: Built-in meta-analysis and statistical tools
- **Collaborative Features**: Multi-researcher collaboration tools
- **Mobile Support**: Mobile-responsive interface development

### Research Applications
- **Medical Research**: Biomedical and clinical systematic reviews
- **Public Health**: Population health and epidemiological studies
- **Healthcare Policy**: Health services and policy research
- **Cross-Disciplinary**: Adaptable to other research domains

---

## WRITING INSTRUCTIONS FOR GPT

When writing about this framework, emphasize:

1. **Innovation**: This is a cutting-edge application of LLMs to systematic review methodology
2. **Comprehensiveness**: The framework covers the entire systematic review pipeline
3. **Intelligence**: Advanced AI features that learn and adapt to user preferences
4. **Practicality**: Real-world application with immediate research benefits
5. **Quality**: Rigorous validation and quality control throughout
6. **Accessibility**: User-friendly interface that doesn't require technical expertise
7. **Extensibility**: Modular design that can be adapted for different research domains
8. **Evidence-Based**: Built on established systematic review methodologies and standards

Focus on how this framework represents a significant advancement in evidence synthesis methodology, combining the rigor of traditional systematic reviews with the efficiency and intelligence of modern AI systems. 