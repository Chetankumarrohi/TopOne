"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";


type RiskOption = {
  value: string;
  label: string;
};


type RiskQuestion = {
  code: string;
  question: string;
  dimension: string;
  options: RiskOption[];
};


type RiskAnswer = {
  question_code: string;
  answer_value: string;
};


type RiskResult = {
  id: number;
  user_id: number;

  capacity_score: number;
  behaviour_score: number;
  horizon_score: number;
  experience_score: number;
  liquidity_score: number;

  final_risk_score: number;
  risk_category: string;

  recommended_equity_min: number;
  recommended_equity_max: number;

  scoring_version: string;
};


export default function RiskAssessmentPage() {
  const router = useRouter();

  const [questions, setQuestions] = useState<RiskQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const [currentQuestion, setCurrentQuestion] = useState(0);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [message, setMessage] = useState("");

  const [existingAssessment, setExistingAssessment] =
    useState(false);

  const [result, setResult] =
    useState<RiskResult | null>(null);


  const progress = useMemo(() => {
    if (questions.length === 0) {
      return 0;
    }

    return Math.round(
      ((currentQuestion + 1) / questions.length) * 100
    );
  }, [currentQuestion, questions.length]);


  useEffect(() => {
    async function loadAssessment() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        router.push("/login");
        return;
      }

      try {
        /*
        -----------------------------------------
        Load questionnaire
        -----------------------------------------
        */

        const questionsResponse = await fetch(
          "/api-backend/risk/questions"
        );

        if (!questionsResponse.ok) {
          setMessage(
            "Could not load the risk questionnaire."
          );
          return;
        }

        const questionData =
          await questionsResponse.json();

        setQuestions(questionData);


        /*
        -----------------------------------------
        Check existing risk profile
        -----------------------------------------
        */

        const profileResponse = await fetch(
          "/api-backend/risk/profile",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (profileResponse.ok) {
          const profileData =
            await profileResponse.json();

          setExistingAssessment(true);

          /*
          Pre-fill previous answers if available
          */

          if (profileData.answers) {
            const previousAnswers: Record<
              string,
              string
            > = {};

            profileData.answers.forEach(
              (answer: {
                question_code: string;
                answer_value: string;
              }) => {
                previousAnswers[
                  answer.question_code
                ] = answer.answer_value;
              }
            );

            setAnswers(previousAnswers);
          }
        }
      } catch {
        setMessage(
          "Could not connect to TopOne."
        );

      } finally {
        setLoading(false);
      }
    }

    loadAssessment();
  }, [router]);


  function selectAnswer(
    questionCode: string,
    value: string
  ) {
    setAnswers((current) => ({
      ...current,
      [questionCode]: value,
    }));

    setMessage("");
  }


  function nextQuestion() {
    const question =
      questions[currentQuestion];

    if (!answers[question.code]) {
      setMessage(
        "Please choose an answer before continuing."
      );

      return;
    }

    setMessage("");

    if (
      currentQuestion <
      questions.length - 1
    ) {
      setCurrentQuestion(
        currentQuestion + 1
      );
    }
  }


  function previousQuestion() {
    setMessage("");

    if (currentQuestion > 0) {
      setCurrentQuestion(
        currentQuestion - 1
      );
    }
  }


  async function submitAssessment() {
    const token =
      localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    /*
    Make sure every question has an answer
    */

    const incomplete = questions.some(
      (question) =>
        !answers[question.code]
    );

    if (incomplete) {
      setMessage(
        "Please answer all questions."
      );

      return;
    }

    setSubmitting(true);
    setMessage("");

    const payload: RiskAnswer[] =
      questions.map((question) => ({
        question_code: question.code,
        answer_value:
          answers[question.code],
      }));

    try {
      const response = await fetch(
        "/api-backend/risk/assessment",
        {
          method: existingAssessment
            ? "PUT"
            : "POST",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${token}`,
          },

          body: JSON.stringify({
            answers: payload,
          }),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        setMessage(
          data.detail ||
            "Could not calculate your risk profile."
        );

        setSubmitting(false);

        return;
      }

      setResult(data);

      setExistingAssessment(true);
    } catch {
      setMessage(
        "Could not connect to the backend."
      );
    } finally {
      setSubmitting(false);
    }
  }


  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] text-white">
        <div className="text-center">

          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/10 border-t-emerald-400" />

          <p className="mt-5 text-sm text-white/45">
            Preparing your risk assessment...
          </p>

        </div>
      </main>
    );
  }


  /*
  -----------------------------------------
  Result screen
  -----------------------------------------
  */

  if (result) {
    return (
      <RiskResultScreen
        result={result}
        onDashboard={() =>
          router.push("/dashboard")
        }
        onReassess={() => {
          setResult(null);
          setCurrentQuestion(0);
        }}
      />
    );
  }


  const question =
    questions[currentQuestion];


  if (!question) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] text-white">
        <p className="text-white/50">
          Risk questionnaire unavailable.
        </p>
      </main>
    );
  }


  return (
    <main className="min-h-screen bg-[#05070b] text-white">

      {/* NAVIGATION */}

      <nav className="border-b border-white/10">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-10">

          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="text-xl font-semibold tracking-tight"
          >
            <span className="text-emerald-300">Top</span>One
          </button>


          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white/60 transition-all duration-300 hover:scale-105 hover:bg-white/[0.08] hover:text-white"
          >
            Exit Assessment
          </button>

        </div>

      </nav>


      {/* ASSESSMENT */}

      <section className="mx-auto max-w-4xl px-6 py-12 sm:py-16">

        <div className="mb-10">

          <div className="flex items-center justify-between">

            <div>
              <p className="text-xs font-medium tracking-[0.18em] text-emerald-300">
                RISK INTELLIGENCE
              </p>

              <p className="mt-2 text-sm text-white/35">
                Question{" "}
                {currentQuestion + 1} of{" "}
                {questions.length}
              </p>
            </div>


            <div className="text-sm font-medium text-white/45">
              {progress}%
            </div>

          </div>


          {/* Progress Bar */}

          <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-white/10">

            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-300 transition-all duration-500"
              style={{
                width: `${progress}%`,
              }}
            />

          </div>

        </div>


        <div className="rounded-[32px] border border-white/10 bg-white/[0.025] p-6 shadow-2xl shadow-emerald-950/10 sm:p-10">

          <div className="mb-3">

            <span className="rounded-full border border-emerald-400/15 bg-emerald-400/[0.06] px-3 py-1.5 text-xs font-medium capitalize text-emerald-300">

              {question.dimension}

            </span>

          </div>


          <h1 className="mt-6 max-w-3xl text-2xl font-semibold leading-snug tracking-tight sm:text-3xl">

            {question.question}

          </h1>


          <div className="mt-8 space-y-3">

            {question.options.map(
              (option) => {

                const selected =
                  answers[
                    question.code
                  ] === option.value;

                return (
                  <button
                    key={
                      option.value
                    }
                    onClick={() =>
                      selectAnswer(
                        question.code,
                        option.value
                      )
                    }
                    className={`
                      group
                      flex
                      w-full
                      items-center
                      justify-between
                      rounded-2xl
                      border
                      px-5
                      py-5
                      text-left
                      transition-all
                      duration-300

                      ${
                        selected
                          ? "border-emerald-400/50 bg-emerald-400/[0.09] shadow-lg shadow-emerald-950/20"
                          : "border-white/10 bg-white/[0.025] hover:scale-[1.01] hover:border-white/20 hover:bg-white/[0.05]"
                      }
                    `}
                  >

                    <div className="flex items-center gap-4">

                      <div
                        className={`
                          flex
                          h-5
                          w-5
                          items-center
                          justify-center
                          rounded-full
                          border
                          transition

                          ${
                            selected
                              ? "border-emerald-400 bg-emerald-400"
                              : "border-white/25"
                          }
                        `}
                      >

                        {selected && (
                          <div className="h-2 w-2 rounded-full bg-[#05070b]" />
                        )}

                      </div>


                      <span
                        className={
                          selected
                            ? "text-white"
                            : "text-white/60"
                        }
                      >
                        {option.label}
                      </span>

                    </div>


                    {selected && (
                      <span className="text-sm text-emerald-300">
                        Selected
                      </span>
                    )}

                  </button>
                );
              }
            )}

          </div>


          {message && (
            <div className="mt-6 rounded-xl border border-amber-400/15 bg-amber-400/[0.05] px-4 py-3 text-sm text-amber-200/80">

              {message}

            </div>
          )}


          <div className="mt-10 flex items-center justify-between">

            <button
              onClick={
                previousQuestion
              }
              disabled={
                currentQuestion === 0
              }
              className="rounded-full border border-white/10 px-6 py-3 text-sm text-white/60 transition-all duration-300 hover:bg-white/[0.06] hover:text-white disabled:cursor-not-allowed disabled:opacity-25"
            >
              ← Previous
            </button>


            {currentQuestion <
            questions.length - 1 ? (

              <button
                onClick={
                  nextQuestion
                }
                className="rounded-full bg-emerald-400 px-7 py-3 font-medium text-black transition-all duration-300 hover:scale-105 hover:bg-emerald-300 active:scale-95"
              >
                Next →
              </button>

            ) : (

              <button
                onClick={
                  submitAssessment
                }
                disabled={
                  submitting
                }
                className="rounded-full bg-emerald-400 px-7 py-3 font-medium text-black transition-all duration-300 hover:scale-105 hover:bg-emerald-300 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
              >

                {submitting
                  ? "Analyzing..."
                  : existingAssessment
                  ? "Recalculate Risk Profile"
                  : "Analyze My Risk"}

              </button>

            )}

          </div>

        </div>


        <p className="mt-7 text-center text-xs leading-5 text-white/25">

          Your answers are combined with your
          financial profile to calculate your
          risk capacity and investment behaviour.

        </p>

      </section>

    </main>
  );
}


/*
==================================================
RESULT SCREEN
==================================================
*/

function RiskResultScreen({
  result,
  onDashboard,
  onReassess,
}: {
  result: RiskResult;
  onDashboard: () => void;
  onReassess: () => void;
}) {

  return (
    <main className="min-h-screen bg-[#05070b] text-white">

      <nav className="border-b border-white/10">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-10">

          <div className="text-xl font-semibold tracking-tight">

            <span className="text-emerald-300">Top</span>One

          </div>


          <button
            onClick={onDashboard}
            className="rounded-full border border-white/10 bg-white/[0.04] px-5 py-2 text-sm text-white/60 transition hover:bg-white/[0.08] hover:text-white"
          >
            Dashboard
          </button>

        </div>

      </nav>


      <section className="mx-auto max-w-5xl px-6 py-14">

        <div className="text-center">

          <p className="text-xs font-medium tracking-[0.18em] text-emerald-300">
            RISK PROFILE COMPLETE
          </p>


          <h1 className="mt-4 text-4xl font-semibold tracking-tight sm:text-5xl">

            Your investor profile is

          </h1>


          <p className="mt-3 text-4xl font-semibold text-emerald-300 sm:text-6xl">

            {result.risk_category}

          </p>

        </div>


        {/* SCORE */}

        <div className="mx-auto mt-10 max-w-xl rounded-[30px] border border-emerald-400/20 bg-emerald-400/[0.05] p-8 text-center">

          <p className="text-sm text-white/40">
            Risk Score
          </p>


          <div className="mt-3">

            <span className="text-6xl font-semibold tracking-tight">
              {Math.round(
                result.final_risk_score
              )}
            </span>

            <span className="ml-2 text-xl text-white/25">
              / 100
            </span>

          </div>


          <div className="mt-7 h-2 overflow-hidden rounded-full bg-white/10">

            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-300"
              style={{
                width: `${Math.min(
                  result.final_risk_score,
                  100
                )}%`,
              }}
            />

          </div>


          <p className="mt-6 text-sm leading-6 text-white/45">

            Your current profile supports an
            indicative equity allocation between{" "}

            <span className="font-medium text-white">
              {result.recommended_equity_min}%
            </span>

            {" "}and{" "}

            <span className="font-medium text-white">
              {result.recommended_equity_max}%
            </span>

            .

          </p>

        </div>


        {/* DIMENSIONS */}

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">

          <ScoreCard
            label="Risk Capacity"
            value={
              result.capacity_score
            }
          />

          <ScoreCard
            label="Behaviour"
            value={
              result.behaviour_score
            }
          />

          <ScoreCard
            label="Horizon"
            value={
              result.horizon_score
            }
          />

          <ScoreCard
            label="Experience"
            value={
              result.experience_score
            }
          />

          <ScoreCard
            label="Liquidity"
            value={
              result.liquidity_score
            }
          />

        </div>


        <div className="mt-8 rounded-[28px] border border-white/10 bg-white/[0.03] p-7">

          <p className="text-sm text-emerald-300">
            What happens next?
          </p>


          <h2 className="mt-3 text-2xl font-medium">

            TopOne now understands your

            financial risk profile.

          </h2>


          <p className="mt-3 max-w-3xl text-sm leading-6 text-white/45">

            Your risk capacity and behaviour will
            later be combined with your goals,
            portfolio, Wealth DNA and Digital Twin
            simulations to produce personalized
            financial recommendations.

          </p>


          <div className="mt-7 flex flex-col gap-3 sm:flex-row">

            <button
              onClick={onDashboard}
              className="rounded-full bg-emerald-400 px-7 py-3 font-medium text-black transition-all duration-300 hover:scale-105 hover:bg-emerald-300 active:scale-95"
            >
              Continue to Dashboard
            </button>


            <button
              onClick={onReassess}
              className="rounded-full border border-white/10 bg-white/[0.04] px-7 py-3 text-sm text-white/70 transition-all duration-300 hover:bg-white/[0.08] hover:text-white"
            >
              Review Answers
            </button>

          </div>

        </div>

      </section>

    </main>
  );
}


/*
==================================================
SCORE CARD
==================================================
*/

function ScoreCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 transition-all duration-300 hover:-translate-y-1 hover:border-emerald-400/20">

      <p className="text-xs text-white/35">
        {label}
      </p>


      <p className="mt-3 text-2xl font-medium">
        {Math.round(value)}
      </p>


      <div className="mt-4 h-1 overflow-hidden rounded-full bg-white/10">

        <div
          className="h-full rounded-full bg-emerald-400"
          style={{
            width: `${Math.min(
              value,
              100
            )}%`,
          }}
        />

      </div>

    </div>
  );
}