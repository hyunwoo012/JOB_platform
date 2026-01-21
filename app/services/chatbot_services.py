class RuleBasedChatbot:
    """Rule-based chatbot - keyword matching"""

    def __init__(self):
        self.intents = {
            "greeting": {
                "keywords": ["hi", "hello", "hey"],
                "responses": [
                    "Hello! How can I help you today?",
                    "Nice to meet you! What can I assist you with?",
                ]
            },
            "job_search": {
                "keywords": ["job", "part-time", "work", "hiring", "opening"],
                "responses": [
                    "You can search for job postings on the main page. You can filter by location, wage, and more!",
                    "To view available part-time jobs, please check the job listings.",
                ]
            },
            "apply": {
                "keywords": ["apply", "application", "how", "method"],
                "responses": [
                    "On the job detail page, click the 'Chat Request' button to start a conversation with the company.",
                    "If you find a job you like, apply by sending a chat request!",
                ]
            },
            "wage": {
                "keywords": ["wage", "pay", "salary", "money", "rate"],
                "responses": [
                    "Each job posting includes wage information. Please check the job details page.",
                    "Wages vary by job. You can find the details on each job posting page.",
                ]
            },
            "profile": {
                "keywords": ["profile", "resume", "information", "education"],
                "responses": [
                    "You can complete your student profile in the 'My Profile' section. Please include your school, major, and skills.",
                    "A well-written profile helps companies find you more easily.",
                ]
            },
            "help": {
                "keywords": ["help", "support", "question", "confused"],
                "responses": [
                    "I can help you with job searches, applications, and chats. What would you like to know?",
                    "From finding a job to applying, I'm here to help. What do you need?",
                ]
            },
        }

        self.default_responses = [
            "Sorry, I didn't quite understand that. Could you please rephrase?",
            "Could you be a bit more specific so I can assist you better?",
            "You can ask about 'job search', 'how to apply', or 'profile setup'.",
        ]

    def get_response(self, message: str) -> str:
        """Generate a response for the given message"""
        import random

        message_lower = message.lower()

        # Match message against intent keywords
        for intent, data in self.intents.items():
            for keyword in data["keywords"]:
                if keyword in message_lower:
                    return random.choice(data["responses"])

        # Fallback response if no keywords match
        return random.choice(self.default_responses)


# Singleton instance
chatbot = RuleBasedChatbot()
