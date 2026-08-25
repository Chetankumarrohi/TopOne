RISK_QUESTIONNAIRE_VERSION = "risk-v1.0"


RISK_QUESTIONS = [
    {
        "code": "LOSS_REACTION",
        "question": "If your investment portfolio falls by 20% in a short period, what would you most likely do?",
        "dimension": "behaviour",
        "options": [
            {
                "value": "SELL_ALL",
                "label": "Sell all investments to avoid further losses",
                "score": 0,
            },
            {
                "value": "SELL_SOME",
                "label": "Sell part of the portfolio",
                "score": 30,
            },
            {
                "value": "HOLD",
                "label": "Hold the investments and wait for recovery",
                "score": 70,
            },
            {
                "value": "BUY_MORE",
                "label": "Invest more at the lower prices",
                "score": 100,
            },
        ],
    },

    {
        "code": "VOLATILITY_COMFORT",
        "question": "How comfortable are you with short-term fluctuations in the value of your investments?",
        "dimension": "behaviour",
        "options": [
            {
                "value": "VERY_UNCOMFORTABLE",
                "label": "Very uncomfortable",
                "score": 0,
            },
            {
                "value": "SOMEWHAT_UNCOMFORTABLE",
                "label": "Somewhat uncomfortable",
                "score": 35,
            },
            {
                "value": "COMFORTABLE",
                "label": "Comfortable",
                "score": 70,
            },
            {
                "value": "VERY_COMFORTABLE",
                "label": "Very comfortable",
                "score": 100,
            },
        ],
    },

    {
        "code": "INVESTMENT_HORIZON",
        "question": "For how long can you keep this money invested before you expect to need it?",
        "dimension": "horizon",
        "options": [
            {
                "value": "LESS_THAN_3_YEARS",
                "label": "Less than 3 years",
                "score": 10,
            },
            {
                "value": "3_TO_5_YEARS",
                "label": "3 to 5 years",
                "score": 40,
            },
            {
                "value": "5_TO_10_YEARS",
                "label": "5 to 10 years",
                "score": 75,
            },
            {
                "value": "MORE_THAN_10_YEARS",
                "label": "More than 10 years",
                "score": 100,
            },
        ],
    },

    {
        "code": "LIQUIDITY_NEED",
        "question": "How likely are you to need a significant portion of this investment unexpectedly?",
        "dimension": "liquidity",
        "options": [
            {
                "value": "VERY_LIKELY",
                "label": "Very likely",
                "score": 10,
            },
            {
                "value": "POSSIBLE",
                "label": "Possible",
                "score": 40,
            },
            {
                "value": "UNLIKELY",
                "label": "Unlikely",
                "score": 75,
            },
            {
                "value": "VERY_UNLIKELY",
                "label": "Very unlikely",
                "score": 100,
            },
        ],
    },

    {
        "code": "INVESTMENT_EXPERIENCE",
        "question": "How would you describe your investment experience?",
        "dimension": "experience",
        "options": [
            {
                "value": "NONE",
                "label": "No previous investment experience",
                "score": 10,
            },
            {
                "value": "BASIC",
                "label": "Basic experience with deposits, SIPs or mutual funds",
                "score": 40,
            },
            {
                "value": "INTERMEDIATE",
                "label": "Experience with mutual funds, ETFs and stocks",
                "score": 70,
            },
            {
                "value": "ADVANCED",
                "label": "Experienced with diversified portfolios and market cycles",
                "score": 100,
            },
        ],
    },

    {
        "code": "RETURN_EXPECTATION",
        "question": "Which statement best describes your return expectations?",
        "dimension": "behaviour",
        "options": [
            {
                "value": "CAPITAL_PROTECTION",
                "label": "Protect my capital even if returns are low",
                "score": 10,
            },
            {
                "value": "STABLE_GROWTH",
                "label": "Prefer stable growth with limited fluctuations",
                "score": 40,
            },
            {
                "value": "BALANCED_GROWTH",
                "label": "Accept moderate fluctuations for better long-term growth",
                "score": 70,
            },
            {
                "value": "HIGH_GROWTH",
                "label": "Accept large fluctuations for potentially higher long-term returns",
                "score": 100,
            },
        ],
    },

    {
        "code": "GOAL_FLEXIBILITY",
        "question": "If your investment performs below expectations, how flexible is your financial goal?",
        "dimension": "behaviour",
        "options": [
            {
                "value": "NOT_FLEXIBLE",
                "label": "The amount and deadline cannot change",
                "score": 10,
            },
            {
                "value": "SLIGHTLY_FLEXIBLE",
                "label": "I can make small adjustments",
                "score": 40,
            },
            {
                "value": "FLEXIBLE",
                "label": "I can increase contributions or extend the deadline",
                "score": 70,
            },
            {
                "value": "VERY_FLEXIBLE",
                "label": "I have substantial flexibility in both amount and timing",
                "score": 100,
            },
        ],
    },
]