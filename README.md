# 🎯 GovOps Pilot - Advanced AI-powered analysis for Indian e-Governance

A unified AWS-based serverless architecture that orchestrates three intelligent micro-agents to optimize IT operations, prevent service disruptions, and reduce costs through automated insights and actions.

## 🎯 Platform Overview

### Three Core Micro-Agents

1. **🧩 SLA Guard Agent** - Predict and prevent SLA breaches using ML-powered monitoring
2. **🤖 Self-Serve L1 Agent** - Automate repetitive technician tasks with safe execution  
3. **💻 Smart Asset & License Optimizer** - Forecast renewals and reduce software waste

### Unified Architecture
- **Serverless**: AWS Lambda, EventBridge, Step Functions
- **Event-Driven**: Real-time cross-agent communication
- **ML-Powered**: SageMaker for intelligent predictions
- **Centralized Analytics**: QuickSight dashboard with sub-minute refresh

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- AWS CDK installed (`npm install -g aws-cdk`)
- Python 3.8+ installed
- Docker (for local testing)

### 1. Deploy the Platform
```bash
git clone <repository>
cd service-efficiency-platform
./deploy.sh
```

### 2. Generate Sample Data
```bash
python3 scripts/generate_sample_data.py
```

### 3. Test SLA Guard Agent
```bash
python3 scripts/generate_sample_data.py --lambda-function sla-guard-metric-processor
```

### 4. Access Dashboard
Visit QuickSight: https://quicksight.aws.amazon.com/

## 🧩 SLA Guard Agent - Detailed Implementation

### Core Features

#### 1. Ticket Monitoring & Ingestion
- **DynamoDB Stream Processing**: Real-time ticket updates
- **JSON/API Integration**: Flexible data source support
- **Automatic Classification**: ML-powered categorization
- **Priority Assessment**: Dynamic priority adjustment

#### 2. ML-Powered Breach Prediction
- **SageMaker Integration**: XGBoost/Linear Learner models
- **Feature Engineering**: 15+ predictive features
- **Confidence Scoring**: Model reliability assessment
- **Real-time Inference**: Sub-2-second predictions

#### 3. Automated Preventive Actions
- **EventBridge Orchestration**: Event-driven triggers
- **Step Functions Workflows**: Complex action sequences
- **SNS/SES Notifications**: Multi-channel alerting
- **Priority Escalation**: Automatic ticket boosting

#### 4. Real-time Dashboard
- **QuickSight Integration**: Executive and operational views
- **Sub-minute Refresh**: Real-time data updates
- **What Next Queue**: Priority-ordered action list
- **SLA Compliance Tracking**: ≥95% adherence target

### Architecture Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Ticket Data   │───▶│  Metric Processor │───▶│  Breach Predictor│
│  (DynamoDB/JSON)│    │     Lambda       │    │     Lambda      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  QuickSight     │◀───│   EventBridge    │───▶│ Action Trigger  │
│   Dashboard     │    │   Custom Bus     │    │     Lambda      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   S3 Data Lake  │◀───│  Status Updater  │    │ Step Functions  │
│   (Analytics)   │    │     Lambda       │    │   Workflows     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Metrics & KPIs

#### SLA Performance
- **Target**: ≥95% SLA adherence
- **Measurement**: Breach prevention rate
- **Alert Threshold**: <90% compliance

#### Prediction Accuracy
- **Target**: >85% ML model accuracy
- **Measurement**: Actual vs predicted breaches
- **Improvement**: Continuous model retraining

#### Response Time
- **Target**: <30 minutes to breach prediction
- **Measurement**: Time from metric update to action
- **Optimization**: Sub-5-second Lambda response

#### Automation Effectiveness
- **Target**: 80% successful preventive actions
- **Measurement**: Actions taken vs breaches prevented
- **ROI**: Time saved vs manual intervention

## 📊 Sample Data & Testing

### Realistic Ticket Scenarios

The platform includes comprehensive sample data generation:

```python
# Critical Infrastructure Issue
{
  "ticket_id": "INC-CRITICAL-001",
  "title": "Email server completely down - all users affected",
  "priority": 1,
  "breach_probability": 0.95,
  "time_to_breach": 3,  # minutes
  "recommended_actions": ["escalate-immediately", "trigger-incident-response"]
}

# Hardware Issue with Medium Risk
{
  "ticket_id": "INC-MEDIUM-003", 
  "title": "3rd floor Marketing printer stuck — jobs queueing",
  "priority": 3,
  "breach_probability": 0.45,
  "time_to_breach": 120,  # minutes
  "recommended_actions": ["assign-senior-tech", "check-spare-parts"]
}
```

### What Next Queue View

Real-time priority queue showing:
- 🔴 **BREACH_IMMINENT** (≥90% probability)
- 🟡 **AT_RISK** (≥70% probability)  
- 🟠 **WATCH** (≥50% probability)
- 🟢 **HEALTHY** (<50% probability)

## 🔧 Configuration

### SLA Thresholds
```json
{
  "priority_1": {"response_time": 15, "resolution_time": 240},
  "priority_2": {"response_time": 60, "resolution_time": 480}, 
  "priority_3": {"response_time": 240, "resolution_time": 1440},
  "priority_4": {"response_time": 480, "resolution_time": 2880},
  "target_adherence": 0.95
}
```

### ML Model Features
- Ticket priority and category
- Historical resolution patterns
- Current system load
- Technician availability
- Time-based patterns
- Escalation history

### Notification Channels
- **SNS Topics**: Real-time alerts
- **SES Email**: Detailed notifications
- **EventBridge**: Cross-agent coordination
- **QuickSight**: Dashboard updates

## 🏗️ Infrastructure

### AWS Services Used
- **Lambda**: Serverless compute (5 functions)
- **EventBridge**: Event-driven architecture
- **DynamoDB**: State management and caching
- **S3**: Data lake for analytics
- **SageMaker**: ML model hosting
- **QuickSight**: Business intelligence
- **Step Functions**: Workflow orchestration
- **SNS/SES**: Notification services
- **CloudWatch**: Monitoring and logging
- **X-Ray**: Distributed tracing

### Cost Optimization
- **Pay-per-use**: Serverless architecture
- **Auto-scaling**: Based on demand
- **Data lifecycle**: S3 intelligent tiering
- **Reserved capacity**: For predictable workloads

## 📈 Expected Results

### SLA Performance Improvement
- **Before**: 85-90% SLA adherence (typical)
- **After**: ≥95% SLA adherence (target)
- **Improvement**: 5-10% increase in compliance

### Operational Efficiency
- **Breach Prevention**: 70-80% of potential breaches avoided
- **Response Time**: 50% faster incident response
- **Manual Effort**: 60% reduction in manual monitoring

### Cost Benefits
- **Prevented Downtime**: $50K-100K per major incident
- **Automation Savings**: 40+ hours/month technician time
- **SLA Penalty Avoidance**: Varies by contract terms

## 🔍 Monitoring & Troubleshooting

### CloudWatch Dashboards
- Lambda function performance
- EventBridge message flow
- DynamoDB read/write capacity
- SageMaker endpoint latency

### Key Alarms
- SLA breach prediction failures
- Lambda function errors
- EventBridge processing delays
- Dashboard refresh failures

### Troubleshooting Guide
1. **High Breach Predictions**: Check system load and ticket volume
2. **ML Model Accuracy**: Retrain with recent data
3. **Notification Delays**: Verify SNS/SES configuration
4. **Dashboard Issues**: Check QuickSight permissions

## 🚀 Future Enhancements

### Phase 2: L1 Automation Integration
- Automated ticket resolution
- Safe execution with rollback
- Integration with existing tools

### Phase 3: Asset Optimization
- License usage analysis
- Cost optimization recommendations
- Renewal forecasting

### Phase 4: Advanced Analytics
- Predictive capacity planning
- Trend analysis and forecasting
- Custom ML model training

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🆘 Support

For support and questions:
- Create an issue in this repository
- Contact the development team
- Check the troubleshooting guide

---

**Built with ❤️ for efficient IT operations**
