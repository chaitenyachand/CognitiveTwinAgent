# Cognitive Twin Agent

### Your AI-Powered Learning Companion

A sophisticated personalized learning platform that leverages Generative AI and Agentic AI to create adaptive, intelligent learning experiences tailored to individual student needs.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [AI Components](#ai-components)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Cognitive Twin Agent is an advanced educational platform that combines cutting-edge AI technologies to provide a truly personalized learning experience. The platform analyzes student performance, identifies knowledge gaps, and dynamically generates customized learning materials to address specific weaknesses.

### What Makes It Unique

- **Adaptive Learning Paths**: AI-driven content generation that responds to individual learning patterns
- **Multi-Modal Content**: Automatic generation of summaries, mind maps, flashcards, and formula sheets
- **Intelligent Assessment**: Dynamic quizzes with mixed question types (MCQ, True/False, Short Answer)
- **Agentic Decision Making**: LangChain-powered agent that analyzes performance and recommends next steps
- **Progress Visualization**: GitHub-style contribution heatmap and detailed analytics

---

## Key Features

### Content Generation
- **Smart Summaries**: AI-generated comprehensive topic summaries from text, PDF, or handwritten notes
- **Interactive Mind Maps**: Visual concept mapping using Markmap for better understanding
- **Adaptive Flashcards**: Key concept cards with flip animations for active recall
- **Formula Sheets**: Automatic extraction and formatting of important equations and definitions

### Learning Assessment
- **Dynamic Quiz Generation**: AI creates contextually relevant questions of varying difficulty
- **Multi-Format Questions**: Supports multiple choice, true/false, and short answer questions
- **Instant Feedback**: Real-time grading with detailed explanations
- **Weak Area Identification**: Automatic detection of topics requiring additional review

### Personalization
- **Cognitive Twin Analysis**: Agentic AI analyzes performance patterns and learning velocity
- **Focused Review Modules**: Targeted content generation for identified weak areas
- **Adaptive Recommendations**: Smart suggestions for next learning steps based on mastery levels
- **Progress Tracking**: Detailed analytics with streak tracking and activity heatmaps

### User Experience
- **Modern UI/UX**: Clean, professional interface with gradient designs and smooth animations
- **Responsive Design**: Works seamlessly across desktop and mobile devices
- **Session Management**: Secure authentication with persistent user sessions
- **Multiple Input Methods**: Accepts typed topics, PDFs, or handwritten notes (OCR)

---

## Technology Stack

### Frontend
- **Streamlit**: Modern Python web framework for rapid UI development
- **Plotly**: Interactive data visualization for progress charts
- **Markmap**: Dynamic mind map rendering
- **Custom CSS**: Tailored styling for professional aesthetics

### Backend
- **Python 3.11**: Core application language
- **MySQL**: Relational database for data persistence
- **OpenAI GPT-4**: Advanced language model for content generation
- **LangChain**: Framework for building AI agents and workflows

### AI & ML
- **OpenAI API**: GPT-4o-mini for efficient content generation
- **EasyOCR**: Optical character recognition for handwritten notes
- **LangChain Agents**: Tool-calling agents for decision making

### Document Processing
- **PyMuPDF (fitz)**: PDF text extraction
- **Pillow (PIL)**: Image processing
- **EasyOCR**: Handwriting recognition

### Security
- **Passlib**: Password hashing with Argon2
- **Session State Management**: Secure user session handling

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit Frontend                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Login     │  │   Dashboard  │  │  Learning Module │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌─────────────┐ │
│  │   Auth   │  │  Utils  │  │ Quiz Gen │  │  Dashboard  │ │
│  └──────────┘  └─────────┘  └──────────┘  └─────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                      AI Services Layer                       │
│  ┌──────────────────┐           ┌───────────────────────┐  │
│  │ Generative AI    │           │    Agentic AI         │  │
│  │ - Summaries      │           │ - Performance Analysis│  │
│  │ - Mind Maps      │           │ - Recommendations     │  │
│  │ - Flashcards     │           │ - Focused Reviews     │  │
│  │ - Quizzes        │           │ - LangChain Agents    │  │
│  └──────────────────┘           └───────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │    MySQL     │  │  OpenAI API  │  │   File Storage   │ │
│  │   Database   │  │              │  │   (Documents)    │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Topic selection or document upload
2. **Content Processing** → Text extraction and preprocessing
3. **AI Generation** → Parallel creation of learning materials
4. **Storage** → Persist data to MySQL database
5. **Assessment** → Generate and administer quizzes
6. **Analysis** → Agentic AI evaluates performance
7. **Adaptation** → Generate focused review content if needed

---

## Installation

### Prerequisites

- Python 3.11 or higher
- MySQL 8.0 or higher
- OpenAI API key
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/cognitive-twin-agent.git
cd cognitive-twin-agent
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up MySQL Database

```sql
CREATE DATABASE cognitive_twin;
CREATE USER 'your_username'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON cognitive_twin.* TO 'your_username'@'localhost';
FLUSH PRIVILEGES;
```

### Step 5: Configure Environment

Create a `config.py` file in the root directory:

```python
# config.py
OPENAI_API_KEY = "your-openai-api-key-here"

# Database Configuration
DB_HOST = "localhost"
DB_USER = "your_username"
DB_PASSWORD = "your_password"
DB_NAME = "cognitive_twin"
```

### Step 6: Initialize Database

The application will automatically create tables on first run, or you can run:

```python
python -c "import database_utils; database_utils.create_tables()"
```

---

## Configuration

### Required Files

- **config.py**: API keys and database credentials
- **background.png**: Login page background image (optional)

### Optional Customization

Modify the following files to customize the experience:

- **app.py**: Main application logic and routing
- **dashboard.py**: Dashboard layout and visualizations
- **generative_ai.py**: AI prompts and generation parameters
- **agentic_ai.py**: Agent behavior and decision logic

---

## Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### User Workflow

#### 1. Registration and Login
- Create an account with username, email, and password
- Secure authentication with Argon2 password hashing

#### 2. Start a New Topic
- Type a topic name
- Upload a PDF document
- Upload handwritten notes (OCR support)
- Select from predefined topics

#### 3. Explore Learning Materials
- View AI-generated summary
- Interact with mind map visualization
- Practice with flashcards
- Reference formula sheets
- Ask questions to the AI tutor

#### 4. Take Quizzes
- Answer dynamically generated questions
- Receive instant feedback
- View correct answers and explanations

#### 5. Review Performance
- Check progress dashboard
- View activity heatmap
- Identify weak topics
- Follow AI recommendations

#### 6. Focused Review
- Study targeted review materials for weak areas
- Retake quizzes to improve mastery
- Track improvement over time

---

## Database Schema

### Users Table
```sql
users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Topics Table
```sql
topics (
    topic_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    source_type ENUM('text', 'pdf', 'predefined', 'ocr'),
    content_summary TEXT,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

### Mindmaps Table
```sql
mindmaps (
    mindmap_id INT PRIMARY KEY AUTO_INCREMENT,
    topic_id INT NOT NULL UNIQUE,
    mindmap_markdown TEXT,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
)
```

### Flashcards Table
```sql
flashcards (
    flashcard_id INT PRIMARY KEY AUTO_INCREMENT,
    topic_id INT NOT NULL UNIQUE,
    flashcard_json JSON,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
)
```

### Formula Sheets Table
```sql
formula_sheets (
    formula_sheet_id INT PRIMARY KEY AUTO_INCREMENT,
    topic_id INT NOT NULL UNIQUE,
    formula_sheet_markdown TEXT,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
)
```

### Quiz Results Table
```sql
quiz_results (
    quiz_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    topic_id INT NOT NULL,
    score DECIMAL(5, 2) NOT NULL,
    total_questions INT NOT NULL,
    weak_areas JSON,
    date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
)
```

### Progress Table
```sql
progress (
    progress_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    total_topics INT DEFAULT 0,
    completed_topics INT DEFAULT 0,
    average_score DECIMAL(5, 2) DEFAULT 0.00,
    weak_topics_list JSON,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

---

## AI Components

### Generative AI Module

**Content Generation Functions:**

- `generate_summary(text)`: Creates comprehensive topic summaries
- `generate_mindmap_markdown(text)`: Produces hierarchical mind map structures
- `generate_flashcards(text)`: Extracts key concepts for flashcards
- `generate_formula_sheet(text)`: Identifies and formats important formulas
- `generate_quiz(text, num_questions)`: Creates mixed-format quizzes
- `answer_question(context, question, style)`: Provides contextual Q&A

### Agentic AI Module

**LangChain Agent Implementation:**

The agent uses two primary tools:

1. **review_weak_topics**: Triggered when score < 70%
   - Generates focused review materials for weak areas
   - Creates new summary, flashcards, and mind map
   - Recommends retaking the quiz

2. **start_new_topic**: Triggered when score >= 70%
   - Congratulates the student on mastery
   - Encourages exploration of new topics

The agent analyzes:
- Quiz performance (score percentage)
- Identified weak areas (topics with incorrect answers)
- Original learning context
- User learning patterns


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **OpenAI**: For providing powerful language models
- **LangChain**: For agent orchestration framework
- **Streamlit**: For rapid web app development
- **Markmap**: For interactive mind map visualization
- **EasyOCR**: For handwriting recognition capabilities


---


**Built with passion for personalized education**

Version 1.0.0 | Last Updated: November 2025
