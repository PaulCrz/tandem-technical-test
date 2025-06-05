# User Flow Analysis - Technical Documentation

## Quick Start Guide

### Prerequisites
- Python 3.7 or higher
- Internet connection (to download data from AWS S3)

### Installation & Setup

#### Option 1: Automated Setup (Recommended)

**For Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**For Windows PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

### Running the Analysis
```bash
# Make sure virtual environment is activated
python user_flow_analyzer.py
```

The script will:
1. Download and process the user events data
2. Analyze user flows and detect anomalies
3. Generate `user_flow_report.html` with visual insights

### Project Structure
```
tandem-technical-test/
├── sources/user_flow_analyzer.py       # Main analysis script
├── requirements.txt                    # Python dependencies
├── setup.sh                            # Linux/macOS setup script
├── setup.ps1                           # Windows PowerShell setup script
├── venv/                               # Virtual environment (created after setup)
└── user_flow_report.html               # Generated report (after running analysis)
```

## Overall Approach

The solution processes user events data to identify meaningful flows and anomalies through a structured pipeline:

1. **Data Loading**: Fetch JSON Lines data from AWS S3 and parse into Python dictionaries
2. **Event Grouping**: Organize events by `user_id` and `session_id` to reconstruct user journeys
3. **Temporal Sorting**: Sort events chronologically within each session to understand flow sequences
4. **Flow Analysis**: Identify successful conversion patterns and abandonment points
5. **Anomaly Detection**: Detect technical errors, user confusion, and unusual behaviors
6. **Report Generation**: Create a visual HTML report with actionable insights for PMs

## Meaningful Flow Identification

### Funnel Analysis
- **Successful Conversions**: Sessions ending with `/checkout` are classified as successful purchases
- **Abandonment Analysis**: Track where users exit without completing the purchase funnel
- **Entry Point Analysis**: Identify the most common starting pages for user sessions

### Pattern Recognition
- Extract path sequences for each session to understand user navigation
- Calculate conversion rates and identify the most effective flow patterns
- Analyze drop-off points to understand where users abandon their journey

## Anomaly Detection Strategy

### 1. Temporal Anomalies
- **Long Gaps**: Detect delays >5 minutes between events, indicating user confusion or technical issues
- **Session Duration**: Flag unusually long or short sessions compared to statistical norms

### 2. Technical Errors
- **Keyword Scanning**: Search CSS selectors and text content for error-related terms (error, 404, timeout, failed)
- **Error Page Analysis**: Identify pages with high error rates

### 3. Behavioral Anomalies
- **High Activity Sessions**: Detect sessions with abnormally high event counts (potential bot traffic or user frustration)
- **Unusual Navigation Patterns**: Identify sessions that deviate significantly from normal user flows

## Scaling and Industrialization Strategy

### Performance Optimization
- **Streaming Processing**: Replace in-memory loading with streaming parsers for large datasets
- **Database Integration**: Use PostgreSQL or similar RDBMS with proper indexing on `user_id`, `session_id`, and `event_time`
- **Parallel Processing**: Implement multiprocessing for independent user session analysis

### Architecture for Production
- **Data Pipeline**: Implement using Apache Airflow or similar orchestration tools
- **Real-time Processing**: Use Apache Kafka + Apache Flink for real-time anomaly detection
- **Caching Layer**: Implement Redis for frequently accessed aggregations
- **Microservices**: Separate flow analysis and anomaly detection into independent services

### Cost Optimization
- **Data Partitioning**: Partition data by date/user for efficient querying
- **Compression**: Use column-store formats like Parquet for better compression ratios
- **Sampling**: Implement intelligent sampling for very large datasets while maintaining statistical significance

### Maintainability
- **Configuration Management**: Externalize anomaly thresholds and flow definitions
- **Monitoring**: Implement comprehensive logging and alerting for pipeline health
- **Testing**: Add unit tests for flow detection logic and anomaly algorithms
- **Documentation**: Maintain detailed API documentation and runbook procedures

### Handling Millions of Events
- **Time-based Processing**: Process events in time windows (hourly/daily) rather than all at once
- **Incremental Updates**: Only reprocess changed data rather than full dataset
- **Distributed Computing**: Use Apache Spark or similar for distributed processing across multiple nodes
- **Data Retention**: Implement tiered storage with hot/warm/cold data lifecycle management

The current implementation serves as a proof-of-concept that can be evolved into a production-ready system by applying these scaling strategies progressively based on actual usage patterns and performance requirements.
