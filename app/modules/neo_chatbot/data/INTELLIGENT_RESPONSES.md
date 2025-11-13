# Intelligent Knowledge Base Response System

## Overview
The Knowledge Base now uses **adaptive response strategies** based on query type classification. No more formulaic, one-size-fits-all answers!

---

## 🎯 Query Types & Response Strategies

### 1. **SIMPLE_FACT** (Short Direct Answers)
**Detection:**
- "What is X?"
- "How many..."
- "When was..."
- "Where is..."
- Yes/No questions

**Response Strategy:**
- Direct answer in 1-3 sentences
- No forced formatting with sections
- Cite source in [brackets]
- Max tokens: 300, Temperature: 0.2 (very focused)

**Example:**
```
Q: "What is NEO?"
A: "NEO is an Automated Storage and Retrieval System (ASRS) that uses 
autonomous robots to store and retrieve bins efficiently in warehouses. 
[NEO System Documentation]"
```

---

### 2. **DEFINITION** (Term Explanations)
**Detection:**
- "What does X mean?"
- "Define X"
- "Definition of..."
- "What is meant by..."

**Response Strategy:**
- Clear definition in 1-2 sentences
- Brief context about usage/importance
- Max tokens: 500, Temperature: 0.3

**Example:**
```
**Definition:** ASRS (Automated Storage and Retrieval System) is a 
warehouse automation technology that uses robotics to automatically 
store and retrieve items.

**Context:** In the NEO system, ASRS enables high-density storage 
and rapid order fulfillment without manual intervention. [NEO Technical Specs]
```

---

### 3. **PROCEDURAL** (How-To Questions)
**Detection:**
- "How to..."
- "How do I..."
- "Steps to..."
- "Procedure for..."
- "Process of..."

**Response Strategy:**
- Numbered step-by-step instructions
- Prerequisites and warnings
- Max tokens: 1000, Temperature: 0.3

**Example:**
```
**How to Configure Bot Charging:**

1. Access the dashboard configuration panel
2. Navigate to Bot Management > Charging Settings
3. Set charging threshold (recommended: 20%)
4. Define charging station locations
5. Save and restart the bot control system

**Important Notes:**
• Ensure power supply is stable before configuration
• Test with one bot before deploying fleet-wide
[Dashboard Manual, Section 4.2]
```

---

### 4. **COMPARISON** (A vs B)
**Detection:**
- "X vs Y"
- "Difference between..."
- "Compare..."
- "Advantages/Disadvantages of..."

**Response Strategy:**
- Structured comparison (table or side-by-side)
- Summary of which is better for what use case
- Max tokens: 800, Temperature: 0.3

**Example:**
```
**Key Differences:**

| Aspect | NEObot | Traditional AGV |
|--------|--------|-----------------|
| Navigation | Swarm intelligence | Fixed tracks |
| Flexibility | High (dynamic routing) | Low (fixed paths) |
| Maintenance | Modular components | Complex systems |

**Summary:** NEObot is better for dynamic warehouses with frequent 
layout changes, while traditional AGV works for fixed processes.
[NEO vs AGV Comparison Document]
```

---

### 5. **EXPLORATORY** (Tell Me About...)
**Detection:**
- "Tell me about..."
- "Explain..."
- "Describe..."
- "Overview of..."
- Long queries (>5 words)

**Response Strategy:**
- Comprehensive structured explanation
- Overview + Key Points + Details
- Multiple sections with formatting
- Max tokens: 1500, Temperature: 0.4

**Example:**
```
**Overview**
The NEO Dashboard is a centralized web interface for monitoring and 
managing the entire warehouse automation system, including bot status, 
order tracking, and performance analytics.

**Key Features**
• Real-time bot location tracking
• Order processing dashboard
• Performance metrics and KPIs
• Alarm management system

**Additional Details**
[Detailed explanation with subsections...]

**Source References**
[Dashboard Manual], [System Architecture Doc]
```

---

### 6. **GENERATIVE** (Create/Generate/Write)
**Detection:**
- "Generate..."
- "Create a..."
- "Write a..."
- "Make a..."
- "Build me..."

**Response Strategy:**
- Politely explain limitation (cannot create new content)
- Offer relevant examples from existing documentation
- Ask what specific information would help
- Max tokens: 400, Temperature: 0.5 (more conversational)

**Example:**
```
Q: "Generate a new techno-commercial offer for Zepto"

A: "I can't generate new techno-commercial offers from scratch, but I can 
help you understand existing offers in the documentation!

I have access to several techno-commercial offer examples:
• DHL NEO Offer (55 pages) - shows system capacity calculations
• ENGINEER-P Commercial Offer - includes detailed component descriptions
• Style Union Offer - demonstrates pricing structure

Would you like me to:
1. Show you the standard structure used in these offers?
2. Explain specific sections (system description, pricing, capacity)?
3. List the key components typically included?

Let me know what specific information would be most helpful!"
```

---

## 🔧 Technical Implementation

### Query Classification (`_classify_query`)
Uses regex patterns and keyword matching to detect:
- Simple fact patterns (regex for "What is X?", "How many", etc.)
- Generative intent ("generate", "create", "write")
- Procedural intent ("how to", "steps to")
- Comparison keywords ("vs", "difference between")
- Exploratory phrases ("tell me about", "explain")

### Adaptive Parameters (`_get_llm_parameters`)
Different max_tokens and temperature for each type:
```python
{
    "SIMPLE_FACT": (300, 0.2),    # Short, very focused
    "DEFINITION": (500, 0.3),     # Medium, precise
    "PROCEDURAL": (1000, 0.3),    # Detailed steps
    "COMPARISON": (800, 0.3),     # Analytical
    "GENERATIVE": (400, 0.5),     # Conversational redirection
    "EXPLORATORY": (1500, 0.4),   # Comprehensive
}
```

### Adaptive System Prompts (`_get_adaptive_system_prompt`)
Each query type has a tailored system prompt with:
- Specific task description
- Response format guidelines
- Examples of expected output
- Rules for handling edge cases

---

## 📊 Benefits

✅ **Natural Responses** - No more forced formatting for simple questions
✅ **Appropriate Length** - Short answers stay short, detailed ones expand
✅ **Smart Handling** - Cannot answer generative requests but offers alternatives
✅ **Better UX** - Users get what they expect based on how they ask
✅ **Token Efficiency** - Don't waste tokens on unnecessary formatting

---

## 🧪 Testing

Run the test script:
```bash
.\venv\Scripts\python.exe app\modules\neo_chatbot\scripts\test_intelligent_responses.py
```

Then restart Flask and try:
1. **Simple:** "What is ASRS?"
2. **Procedural:** "How to configure bots?"
3. **Generative:** "Generate a proposal for Zepto"
4. **Exploratory:** "Tell me about the NEO system"

---

## 🚀 Future Enhancements

- Multi-turn conversation tracking
- Dynamic confidence thresholds per query type
- Language detection for multi-lingual support
- Query intent clarification ("Did you mean...?")
- Automatic follow-up question generation
