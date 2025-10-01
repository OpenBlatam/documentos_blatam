# 🔌 Neural Marketing Consciousness System - API Documentation

## 📋 Overview

The Neural Marketing Consciousness System API provides comprehensive access to all platform features including consciousness assessment, learning management, tool integration, and community features. This documentation covers all available endpoints, authentication, and usage examples.

## 🔐 Authentication

### API Key Authentication

All API requests require authentication using an API key in the header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Getting Your API Key

1. **Log in to your account** at [neuralmarketingconsciousness.com]
2. **Navigate to Settings > API Keys**
3. **Generate a new API key** for your application
4. **Store the key securely** - it won't be shown again

### Rate Limiting

- **Free Tier:** 100 requests per hour
- **Basic Tier:** 1,000 requests per hour
- **Professional Tier:** 10,000 requests per hour
- **Enterprise Tier:** 100,000 requests per hour

## 🌐 Base URL

```
https://api.neuralmarketingconsciousness.com/v1
```

## 📊 Consciousness Assessment API

### Start Assessment

Start a new consciousness assessment session.

```http
POST /assessment/start
```

#### Request Body
```json
{
  "user_id": "string",
  "assessment_type": "full" | "quick" | "focused",
  "language": "en" | "es" | "fr" | "de" | "pt" | "zh"
}
```

#### Response
```json
{
  "session_id": "uuid",
  "assessment_id": "uuid",
  "questions": [
    {
      "id": "string",
      "question": "string",
      "type": "multiple_choice" | "scale" | "text",
      "options": ["string"],
      "category": "technical" | "strategic" | "ethical" | "creative" | "leadership"
    }
  ],
  "total_questions": 100,
  "estimated_duration": 30
}
```

### Submit Assessment

Submit assessment responses and get results.

```http
POST /assessment/submit
```

#### Request Body
```json
{
  "session_id": "uuid",
  "responses": [
    {
      "question_id": "string",
      "answer": "string" | number,
      "confidence": 1-10
    }
  ]
}
```

#### Response
```json
{
  "assessment_result": {
    "consciousness_level": 75,
    "archetype": "visionary",
    "confidence_score": 0.92,
    "category_scores": {
      "technical": 80,
      "strategic": 85,
      "ethical": 70,
      "creative": 90,
      "leadership": 75
    },
    "recommendations": [
      {
        "category": "technical",
        "priority": "high",
        "action": "Complete advanced AI tools course",
        "estimated_impact": 15
      }
    ],
    "learning_path": {
      "recommended_tier": "specialist",
      "estimated_duration": "8 weeks",
      "next_steps": ["Complete foundation webinars", "Start tool integration"]
    }
  }
}
```

### Get Assessment History

Retrieve user's assessment history.

```http
GET /assessment/history/{user_id}
```

#### Query Parameters
- `limit` (optional): Number of results to return (default: 10)
- `offset` (optional): Number of results to skip (default: 0)

#### Response
```json
{
  "assessments": [
    {
      "assessment_id": "uuid",
      "date": "2024-01-15T10:30:00Z",
      "consciousness_level": 75,
      "archetype": "visionary",
      "improvement": 5
    }
  ],
  "total_count": 25,
  "average_consciousness_level": 72,
  "improvement_trend": "positive"
}
```

## 🎓 Learning Management API

### Get Learning Path

Get personalized learning path for user.

```http
GET /learning/path/{user_id}
```

#### Response
```json
{
  "user_id": "string",
  "current_tier": "specialist",
  "consciousness_level": 65,
  "learning_path": {
    "tier": "specialist",
    "duration": "8 weeks",
    "modules": [
      {
        "id": "string",
        "title": "Advanced AI Content Creation",
        "type": "webinar",
        "duration": 120,
        "consciousness_level_required": 60,
        "status": "not_started" | "in_progress" | "completed",
        "progress": 0
      }
    ],
    "prerequisites": ["Complete foundation webinars"],
    "estimated_completion": "2024-03-15"
  }
}
```

### Update Learning Progress

Update user's learning progress.

```http
POST /learning/progress
```

#### Request Body
```json
{
  "user_id": "string",
  "module_id": "string",
  "progress_percentage": 75,
  "time_spent": 90,
  "notes": "string",
  "completed": false
}
```

#### Response
```json
{
  "success": true,
  "updated_progress": {
    "module_id": "string",
    "progress_percentage": 75,
    "time_spent": 90,
    "completion_date": null,
    "next_module": "string"
  },
  "consciousness_impact": 2.5
}
```

### Get Learning Analytics

Get detailed learning analytics for user.

```http
GET /learning/analytics/{user_id}
```

#### Query Parameters
- `start_date` (optional): Start date for analytics (ISO 8601)
- `end_date` (optional): End date for analytics (ISO 8601)
- `granularity` (optional): "daily" | "weekly" | "monthly" (default: "weekly")

#### Response
```json
{
  "user_id": "string",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "metrics": {
    "total_learning_time": 1200,
    "modules_completed": 8,
    "consciousness_improvement": 15,
    "average_session_duration": 45,
    "completion_rate": 0.85
  },
  "trends": [
    {
      "date": "2024-01-01",
      "consciousness_level": 60,
      "learning_time": 60,
      "modules_completed": 1
    }
  ],
  "recommendations": [
    {
      "type": "learning_velocity",
      "message": "Consider increasing daily learning time to 60 minutes",
      "priority": "medium"
    }
  ]
}
```

## 🛠️ Tool Integration API

### Get Available Tools

Get list of available AI marketing tools.

```http
GET /tools
```

#### Query Parameters
- `category` (optional): Filter by tool category
- `consciousness_level` (optional): Filter by required consciousness level
- `search` (optional): Search term for tool names

#### Response
```json
{
  "tools": [
    {
      "id": "gpt4-integration",
      "name": "GPT-4 Integration",
      "category": "content_creation",
      "description": "Advanced text generation and content creation",
      "consciousness_level_required": 20,
      "capabilities": ["content_writing", "copywriting", "translation"],
      "api_endpoint": "/api/tools/gpt4",
      "documentation_url": "https://docs.neuralmarketingconsciousness.com/tools/gpt4",
      "pricing": {
        "free_tier": "100 requests/month",
        "paid_tier": "$0.01 per request"
      }
    }
  ],
  "total_count": 150,
  "categories": ["content_creation", "analytics", "automation", "personalization"]
}
```

### Execute Tool

Execute an AI marketing tool.

```http
POST /tools/execute
```

#### Request Body
```json
{
  "user_id": "string",
  "tool_id": "gpt4-integration",
  "parameters": {
    "prompt": "Write a marketing email for our new product launch",
    "tone": "professional",
    "length": "medium",
    "target_audience": "B2B professionals"
  },
  "context": {
    "campaign_id": "string",
    "brand_voice": "string"
  }
}
```

#### Response
```json
{
  "execution_id": "uuid",
  "tool_id": "gpt4-integration",
  "status": "completed" | "processing" | "failed",
  "result": {
    "content": "Subject: Introducing Our Revolutionary New Product...",
    "metadata": {
      "word_count": 250,
      "tone_score": 0.85,
      "readability_score": 0.78
    }
  },
  "consciousness_impact": 1.2,
  "execution_time": 2.5,
  "cost": 0.05
}
```

### Get Tool Usage Analytics

Get analytics for tool usage.

```http
GET /tools/analytics/{user_id}
```

#### Query Parameters
- `tool_id` (optional): Filter by specific tool
- `start_date` (optional): Start date for analytics
- `end_date` (optional): End date for analytics

#### Response
```json
{
  "user_id": "string",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "tool_usage": [
    {
      "tool_id": "gpt4-integration",
      "tool_name": "GPT-4 Integration",
      "usage_count": 45,
      "total_cost": 2.25,
      "consciousness_impact": 12.5,
      "success_rate": 0.95,
      "average_execution_time": 2.1
    }
  ],
  "total_usage": {
    "tools_used": 12,
    "total_executions": 150,
    "total_cost": 15.75,
    "total_consciousness_impact": 45.2
  }
}
```

## 👥 Community API

### Get Community Posts

Get community posts and discussions.

```http
GET /community/posts
```

#### Query Parameters
- `category` (optional): Filter by post category
- `consciousness_level` (optional): Filter by consciousness level
- `limit` (optional): Number of posts to return (default: 20)
- `offset` (optional): Number of posts to skip (default: 0)

#### Response
```json
{
  "posts": [
    {
      "post_id": "uuid",
      "user_id": "string",
      "username": "string",
      "consciousness_level": 75,
      "title": "Best practices for AI content creation",
      "content": "I've been using GPT-4 for content creation...",
      "category": "content_creation",
      "tags": ["gpt4", "content", "best_practices"],
      "likes": 25,
      "comments": 8,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 150,
  "has_more": true
}
```

### Create Community Post

Create a new community post.

```http
POST /community/posts
```

#### Request Body
```json
{
  "user_id": "string",
  "title": "string",
  "content": "string",
  "category": "content_creation" | "tools" | "strategy" | "general",
  "tags": ["string"],
  "is_question": false
}
```

#### Response
```json
{
  "post_id": "uuid",
  "success": true,
  "message": "Post created successfully"
}
```

### Get User Profile

Get user profile information.

```http
GET /users/{user_id}
```

#### Response
```json
{
  "user_id": "string",
  "username": "string",
  "email": "string",
  "consciousness_level": 75,
  "archetype": "visionary",
  "tier": "specialist",
  "join_date": "2024-01-01T00:00:00Z",
  "last_active": "2024-01-15T10:30:00Z",
  "achievements": [
    {
      "id": "string",
      "name": "Consciousness Pioneer",
      "description": "Reached 50% consciousness level",
      "earned_date": "2024-01-10T00:00:00Z"
    }
  ],
  "stats": {
    "total_learning_time": 1200,
    "modules_completed": 8,
    "tools_used": 12,
    "community_posts": 25,
    "helpful_posts": 15
  }
}
```

## 📊 Analytics API

### Get Dashboard Data

Get comprehensive dashboard data for user.

```http
GET /dashboard/{user_id}
```

#### Response
```json
{
  "user_id": "string",
  "consciousness": {
    "current_level": 75,
    "target_level": 80,
    "progress_percentage": 85,
    "improvement_trend": "positive",
    "next_milestone": {
      "level": 80,
      "description": "Advanced Specialist",
      "estimated_date": "2024-02-15"
    }
  },
  "learning": {
    "current_module": "Advanced AI Content Creation",
    "progress_percentage": 60,
    "time_spent_today": 45,
    "weekly_goal": 300,
    "weekly_progress": 180
  },
  "tools": {
    "most_used": [
      {
        "tool_id": "gpt4-integration",
        "name": "GPT-4 Integration",
        "usage_count": 25
      }
    ],
    "recent_activity": [
      {
        "tool_id": "gpt4-integration",
        "action": "content_generation",
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  },
  "community": {
    "posts_this_week": 3,
    "likes_received": 15,
    "helpful_responses": 5,
    "reputation_score": 85
  }
}
```

### Get Consciousness Trends

Get consciousness development trends over time.

```http
GET /analytics/consciousness-trends/{user_id}
```

#### Query Parameters
- `start_date` (optional): Start date for trends
- `end_date` (optional): End date for trends
- `granularity` (optional): "daily" | "weekly" | "monthly"

#### Response
```json
{
  "user_id": "string",
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "trends": [
    {
      "date": "2024-01-01",
      "consciousness_level": 60,
      "learning_time": 60,
      "tool_usage": 5,
      "community_engagement": 2
    }
  ],
  "insights": [
    {
      "type": "growth_acceleration",
      "message": "Your consciousness level increased 15% this month",
      "priority": "high"
    }
  ],
  "predictions": {
    "next_month_consciousness": 78,
    "confidence": 0.85
  }
}
```

## 🔔 Notifications API

### Get Notifications

Get user notifications.

```http
GET /notifications/{user_id}
```

#### Query Parameters
- `status` (optional): "unread" | "read" | "all" (default: "unread")
- `limit` (optional): Number of notifications to return (default: 20)

#### Response
```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "learning_reminder" | "achievement" | "community" | "system",
      "title": "New module available",
      "message": "Advanced AI Content Creation module is now available",
      "status": "unread",
      "created_at": "2024-01-15T10:30:00Z",
      "action_url": "/learning/modules/advanced-ai-content-creation"
    }
  ],
  "unread_count": 5
}
```

### Mark Notification as Read

Mark a notification as read.

```http
PUT /notifications/{notification_id}/read
```

#### Response
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

## 🎯 Error Handling

### Error Response Format

All API errors follow this format:

```json
{
  "error": {
    "code": "INSUFFICIENT_CONSCIOUSNESS",
    "message": "Consciousness level too low for this action",
    "details": {
      "required_level": 70,
      "current_level": 65
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "uuid"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_API_KEY` | 401 | Invalid or missing API key |
| `INSUFFICIENT_CONSCIOUSNESS` | 403 | Consciousness level too low |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `RESOURCE_NOT_FOUND` | 404 | Resource not found |
| `INTERNAL_ERROR` | 500 | Internal server error |

### Rate Limiting

When rate limits are exceeded, the API returns:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_time": "2024-01-15T11:00:00Z"
    }
  }
}
```

## 📝 SDKs and Libraries

### Official SDKs

#### Python SDK
```bash
pip install neural-marketing-consciousness
```

```python
from neural_marketing_consciousness import ConsciousnessClient

client = ConsciousnessClient(api_key="your_api_key")

# Start assessment
assessment = client.assessment.start(user_id="user123")

# Submit responses
result = client.assessment.submit(
    session_id=assessment.session_id,
    responses=responses
)

# Execute tool
tool_result = client.tools.execute(
    user_id="user123",
    tool_id="gpt4-integration",
    parameters={"prompt": "Write a marketing email"}
)
```

#### JavaScript SDK
```bash
npm install neural-marketing-consciousness
```

```javascript
import { ConsciousnessClient } from 'neural-marketing-consciousness';

const client = new ConsciousnessClient('your_api_key');

// Start assessment
const assessment = await client.assessment.start('user123');

// Submit responses
const result = await client.assessment.submit(
  assessment.session_id,
  responses
);

// Execute tool
const toolResult = await client.tools.execute('user123', 'gpt4-integration', {
  prompt: 'Write a marketing email'
});
```

## 🔧 Webhooks

### Webhook Events

The API supports webhooks for real-time notifications:

- `assessment.completed` - Assessment completed
- `consciousness.level_changed` - Consciousness level changed
- `learning.module_completed` - Learning module completed
- `tool.executed` - Tool executed
- `community.post_created` - Community post created

### Webhook Configuration

```http
POST /webhooks
```

#### Request Body
```json
{
  "url": "https://your-app.com/webhooks/consciousness",
  "events": ["assessment.completed", "consciousness.level_changed"],
  "secret": "your_webhook_secret"
}
```

### Webhook Payload

```json
{
  "event": "assessment.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "user_id": "string",
    "assessment_id": "uuid",
    "consciousness_level": 75,
    "archetype": "visionary"
  }
}
```

## 📚 Examples

### Complete Assessment Flow

```python
from neural_marketing_consciousness import ConsciousnessClient

client = ConsciousnessClient(api_key="your_api_key")

# 1. Start assessment
assessment = client.assessment.start(
    user_id="user123",
    assessment_type="full"
)

# 2. Answer questions (simplified)
responses = []
for question in assessment.questions:
    # In real implementation, collect user input
    response = {
        "question_id": question["id"],
        "answer": "sample_answer",
        "confidence": 8
    }
    responses.append(response)

# 3. Submit assessment
result = client.assessment.submit(
    session_id=assessment.session_id,
    responses=responses
)

print(f"Consciousness Level: {result.consciousness_level}")
print(f"Archetype: {result.archetype}")
```

### Tool Execution Example

```python
# Execute GPT-4 integration
tool_result = client.tools.execute(
    user_id="user123",
    tool_id="gpt4-integration",
    parameters={
        "prompt": "Write a marketing email for our new AI product",
        "tone": "professional",
        "length": "medium",
        "target_audience": "B2B professionals"
    }
)

print(f"Generated Content: {tool_result.result['content']}")
print(f"Consciousness Impact: {tool_result.consciousness_impact}")
```

---

*For more information, visit our [developer documentation](https://developers.neuralmarketingconsciousness.com) or contact our API support team.*