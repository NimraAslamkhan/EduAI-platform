"""
Groq AI Chatbot - School Intelligence Chatbot using llama-3.3-70b-versatile.
"""

import os
import logging
import streamlit as st
from src.config.api_keys import load_api_keys

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 12  # Keep last 12 messages for context


class SchoolChatbot:
    """AI chatbot for school intelligence using Groq API."""

    def __init__(self):
        # Load API key from keys file (optional) or environment variable.
        keys = load_api_keys()
        self.api_key = keys.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY", "")
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize Groq client if API key is available."""
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. Chatbot will use fallback responses.")
            return
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            logger.info("Groq client initialized successfully")
        except ImportError:
            logger.error("groq package not installed. Run: pip install groq")
        except Exception as e:
            logger.error(f"Groq client initialization error: {e}")

    def _build_system_prompt(self, context: dict) -> str:
        """Build a dynamic system prompt with school data context."""
        school_info = context.get("school_info", {})
        stats = context.get("stats", {})

        return f"""You are EduAI, an intelligent school management assistant for {school_info.get('school_name', 'the school')}.

You help school staff, principals, and teachers understand student performance, attendance patterns,
and provide actionable recommendations.

CURRENT SCHOOL STATISTICS:
- Total Students: {stats.get('total_students', 'N/A')}
- Total Teachers: {stats.get('total_teachers', 'N/A')}
- Overall Attendance Rate: {stats.get('attendance_rate', 'N/A')}%
- Average Academic Score: {stats.get('avg_marks', 'N/A')}%
- Active AI Alerts: {stats.get('active_alerts', 'N/A')}

YOUR CAPABILITIES:
- Analyze student performance trends and identify weak students
- Explain attendance patterns and correlations with academic performance
- Suggest intervention strategies for at-risk students
- Provide class-level and school-level analytics insights
- Generate improvement plans for students, teachers, and the school

GUIDELINES:
- Be concise, data-driven, and actionable
- Use the school statistics provided when answering questions
- If you don't have specific data, say so and provide general best practices
- Format responses clearly with bullet points where helpful
- Always be empathetic when discussing struggling students
- Do not make up specific student names or fabricate data
"""

    def _get_fallback_response(self, message: str) -> str:
        """Rule-based fallback when Groq API is unavailable."""
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["weak", "failing", "fail", "struggling", "risk"]):
            return """**Identifying At-Risk Students** 📊

Based on our data analysis, students at risk typically show these patterns:
- **Attendance below 75%** — Strong predictor of academic failure
- **Average scores below 50%** — Requires immediate intervention
- **Low study hours (<2 hrs/day)** — Correlates with poor performance

**Recommended Actions:**
1. Schedule one-on-one meetings with struggling students
2. Notify parents within 48 hours of identifying risk
3. Assign peer tutoring for failing subjects
4. Set weekly check-in goals and track progress

Use the AI Predictions tab to see the full dropout risk analysis."""

        elif any(w in msg_lower for w in ["attendance", "absent", "present"]):
            return """**Attendance Insights** 📅

Attendance is the #1 predictor of academic success in our analysis:

- **Above 90%** → Student likely to perform well (avg score: 78%)
- **75-90%** → Moderate performance risk
- **Below 75%** → High academic failure risk
- **Below 60%** → Critical — dropout risk is very high

**Quick Interventions:**
1. Send automated SMS alerts to parents after 2 consecutive absences
2. Assign an attendance mentor to chronic absentees
3. Create flexible catch-up schedules
4. Investigate root causes (health, transport, family issues)"""

        elif any(w in msg_lower for w in ["improve", "improvement", "better", "recommendation"]):
            return """**Improvement Recommendations** 🚀

**For Students:**
1. Increase daily study hours from current average to 4+ hours
2. Focus on weakest subjects first (use subject radar chart)
3. Form study groups for collaborative learning

**For Teachers:**
1. Use differentiated instruction for mixed-ability classes
2. Increase formative assessments (weekly quizzes)
3. Provide detailed feedback on returned assignments

**For School Leadership:**
1. Launch a mentorship program pairing senior and junior students
2. Invest in digital learning tools for self-paced study
3. Host monthly parent-teacher conferences for at-risk families"""

        elif any(w in msg_lower for w in ["class", "performance", "subject", "math", "science"]):
            return """**Class Performance Analysis** 🏫

To identify class-level issues, look for:
- **Below-average attendance** → Systemic issue (teacher, schedule, environment)
- **Subject-specific failures** → Curriculum or teaching methodology issue
- **Sudden drops** → May indicate external factor (weather, events, teacher absence)

**Diagnostic Questions:**
1. Has there been a teacher change recently?
2. Are multiple classes failing the same subject?
3. When did the decline start?

Check the Class Comparison chart and Subject Performance Radar in Analytics for visual insights."""

        elif any(w in msg_lower for w in ["dropout", "risk", "retention"]):
            return """**Dropout Risk Management** ⚠️

Our AI model identifies dropout risk using:
- Academic performance (weight: 40%)
- Attendance rate (weight: 40%)
- Study hours per day (weight: 20%)

**Risk Levels:**
- 🟢 Low (<30%): Continue monitoring
- 🟡 Medium (30-60%): Parent notification + counseling
- 🔴 High (>60%): Immediate intervention team required

**Prevention Strategies:**
1. Early warning system (monthly ML predictions)
2. Student success coaches for high-risk students
3. Financial aid review for fee-defaulting families
4. Mental health support resources"""

        else:
            return """**Welcome to EduAI Assistant** 🎓

I can help you with:
- **"Which students need support?"** — Identify at-risk students
- **"Why is Class 8 performing poorly?"** — Class-level analysis
- **"Suggest an improvement plan"** — Actionable recommendations
- **"What's the attendance situation?"** — Attendance insights
- **"How to reduce dropout risk?"** — Retention strategies

Ask me anything about your school's performance data!"""

    def chat(self, message: str, history: list, context: dict = None) -> str:
        """
        Send a message to Groq and get a response.
        
        Args:
            message: User's message
            history: List of {"role": str, "content": str} dicts
            context: Dict with school statistics and info
            
        Returns:
            AI response as string
        """
        if not self.client:
            return self._get_fallback_response(message)

        try:
            system_prompt = self._build_system_prompt(context or {})

            # Build messages list
            messages = [{"role": "system", "content": system_prompt}]

            # Add recent history (last MAX_HISTORY messages)
            for msg in history[-MAX_HISTORY:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            # Add current message
            messages.append({"role": "user", "content": message})

            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                top_p=0.9,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"⚠️ AI temporarily unavailable. Using smart fallback:\n\n{self._get_fallback_response(message)}"


def render_chatbot_ui(context: dict = None):
    """Render the full chatbot UI with chat history and input."""
    from src.components.ui_components import section_header

    section_header("AI Assistant", "Powered by Groq llama-3.3-70b-versatile", "🤖")

    chatbot = SchoolChatbot()
    api_configured = bool(chatbot.api_key)

    if not api_configured:
        st.warning("""
        ⚠️ **Groq API key not configured.** The chatbot is running with smart rule-based fallback responses.
        
        To enable full AI: Add `GROQ_API_KEY` to your environment secrets and restart the app.
        """)

    # Chat history container
    chat_container = st.container()

    with chat_container:
        if not st.session_state.get("chat_history"):
            st.markdown("""
            <div style="background: linear-gradient(135deg,#0d1226,#111827); border:1px solid #1e2a45;
                        border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 16px;">
                <div style="font-size: 2.5rem; margin-bottom: 12px;">🤖</div>
                <h3 style="color:#ccd6f6; margin:0 0 8px 0;">EduAI Assistant</h3>
                <p style="color:#8892b0; font-size:0.9rem; margin:0;">
                    Ask me about student performance, attendance trends, weak students, 
                    improvement recommendations, or any school analytics.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Suggestion buttons
            st.markdown("**💡 Try asking:**")
            suggestions = [
                "Which students need immediate support?",
                "Why is attendance declining?",
                "Suggest an improvement plan for weak students",
                "How can we reduce dropout risk?",
            ]
            cols = st.columns(2)
            for i, suggestion in enumerate(suggestions):
                with cols[i % 2]:
                    if st.button(f"💬 {suggestion}", key=f"sugg_{i}", use_container_width=True):
                        st.session_state.chat_history = st.session_state.get("chat_history", [])
                        response = chatbot.chat(suggestion, [], context or {})
                        st.session_state.chat_history.append({"role": "user", "content": suggestion})
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.rerun()
        else:
            # Display conversation
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about student performance, attendance, or get recommendations..."):
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Show user message immediately
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)

        # Get AI response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                response = chatbot.chat(prompt, st.session_state.chat_history, context or {})
            st.markdown(response)

        # Save to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Clear history button
    if st.session_state.get("chat_history"):
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
