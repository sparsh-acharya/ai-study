"""
AI-powered quiz generation using LangChain + Gemini
=====================================================
Uses the RAG pipeline's LLM helper (no document retrieval needed for
quiz generation — the topic context comes from the database).
"""

import json
import logging

from pdf.models import Quiz, Question, Answer, StudyPlan, StudyWeek
from rag_pipeline import process_text_with_llm

logger = logging.getLogger("quiz_generator")


def generate_quiz_for_week(study_week, difficulty='medium', num_questions=10):
    """
    Generate a quiz for a specific study week using the LLM.

    Args:
        study_week: StudyWeek instance
        difficulty: 'easy', 'medium', or 'hard'
        num_questions: Number of questions to generate

    Returns:
        Quiz instance with questions and answers
    """
    try:
        # Build the prompt from structured DB data
        prompt = get_quiz_generation_prompt(study_week, difficulty, num_questions)

        logger.info(
            "🎯 Generating %s quiz (%d questions) for Week %d: %s",
            difficulty, num_questions, study_week.week_number, study_week.topic,
        )

        # Use the lightweight text-only LLM call (no RAG retrieval needed)
        response_text = process_text_with_llm(prompt)

        # Parse the response
        quiz_data = json.loads(response_text)
        logger.info("✅ Quiz JSON parsed successfully")

        # Create Quiz object
        quiz = Quiz.objects.create(
            study_plan=study_week.study_plan,
            study_week=study_week,
            title=quiz_data.get('title', f"Week {study_week.week_number} Quiz: {study_week.topic}"),
            description=quiz_data.get('description', f"Test your knowledge on {study_week.topic}"),
            difficulty=difficulty,
            time_limit_minutes=quiz_data.get('time_limit_minutes', num_questions * 2),
            passing_score=quiz_data.get('passing_score', 70),
            xp_reward=calculate_xp_reward(difficulty, num_questions)
        )

        # Create questions and answers
        for idx, q_data in enumerate(quiz_data.get('questions', []), 1):
            question = Question.objects.create(
                quiz=quiz,
                question_text=q_data['question'],
                question_type=q_data.get('type', 'multiple_choice'),
                explanation=q_data.get('explanation', ''),
                points=q_data.get('points', 1),
                order=idx
            )

            # Create answers
            for ans_idx, ans_data in enumerate(q_data.get('answers', []), 1):
                Answer.objects.create(
                    question=question,
                    answer_text=ans_data['text'],
                    is_correct=ans_data.get('is_correct', False),
                    order=ans_idx
                )

        logger.info("✅ Quiz created: %s (%d questions)", quiz.title, quiz.total_questions)
        return quiz

    except json.JSONDecodeError as e:
        logger.error("❌ Failed to parse quiz JSON: %s", e)
        raise
    except Exception as e:
        logger.error("❌ Error generating quiz: %s", e)
        raise


def get_quiz_generation_prompt(study_week, difficulty, num_questions):
    """Generate the prompt for quiz creation."""

    # Get activities for context
    activities = study_week.activities.all()
    activities_text = "\n".join([f"- {act.description}" for act in activities])

    difficulty_instructions = {
        'easy': 'Focus on basic recall and understanding. Questions should test fundamental concepts.',
        'medium': 'Mix of recall, application, and analysis. Questions should require understanding and application.',
        'hard': 'Advanced application, analysis, and synthesis. Questions should be challenging and require deep understanding.'
    }

    prompt = f"""You are an expert educational assessment designer. Create a {difficulty} difficulty quiz for the following study topic:

**Topic:** {study_week.topic}
**Week:** {study_week.week_number}

**Learning Activities:**
{activities_text}

**Quiz Requirements:**
- Generate exactly {num_questions} multiple-choice questions
- Difficulty level: {difficulty} - {difficulty_instructions.get(difficulty, '')}
- Each question should have 4 answer options
- Only ONE answer should be correct
- Include a brief explanation for each correct answer
- Questions should cover different aspects of the topic
- Make questions practical and relevant to real-world applications when possible

**Output Format (JSON):**
{{
  "title": "Engaging quiz title",
  "description": "Brief description of what the quiz covers",
  "time_limit_minutes": {num_questions * 2},
  "passing_score": 70,
  "questions": [
    {{
      "question": "Clear, specific question text",
      "type": "multiple_choice",
      "answers": [
        {{"text": "Answer option 1", "is_correct": false}},
        {{"text": "Answer option 2", "is_correct": true}},
        {{"text": "Answer option 3", "is_correct": false}},
        {{"text": "Answer option 4", "is_correct": false}}
      ],
      "explanation": "Why the correct answer is right and what concept it tests",
      "points": 1
    }}
  ]
}}

Generate a high-quality, educational quiz now."""

    return prompt


def calculate_xp_reward(difficulty, num_questions):
    """Calculate XP reward based on difficulty and number of questions."""
    base_xp = {
        'easy': 2,
        'medium': 3,
        'hard': 5
    }
    return base_xp.get(difficulty, 3) * num_questions
