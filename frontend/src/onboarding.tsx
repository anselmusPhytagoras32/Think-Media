// FR01–05 / NFR05/09: optional first-use orientation; persistence belongs to App.
import { useEffect, useRef, useState } from "react";
import { BrandMark, ThinkIcon } from "./brand";
import { Artwork, type ArtworkKind } from "./artwork";
import type { IconName } from "./brand";

const steps: {
  title: string;
  description: string;
  note: string;
  label: string;
  icon: IconName;
  artwork: ArtworkKind;
}[] = [
  {
    title: "Get ready for your OJT.",
    description:
      "Learn workplace skills, save useful resources and check what you know with short quizzes. Take it one step at a time.",
    note: "A place for students, instructors and participating companies.",
    label: "Prepare",
    icon: "learning",
    artwork: "welcome",
  },
  {
    title: "Find an opportunity that fits.",
    description:
      "Explore OJT and job listings from verified companies. Search by location, type or skill, then read the requirements before you apply.",
    note: "Suggestions help you explore. Companies make their own application decisions.",
    label: "Explore",
    icon: "opportunities",
    artwork: "opportunities",
  },
  {
    title: "Keep every application in view.",
    description:
      "Review your PDF and cover letter before sending. Then follow your application’s status and history in one place.",
    note: "Your application documents are shared only with the company reviewing them.",
    label: "Apply",
    icon: "applications",
    artwork: "applications",
  },
];

export function Onboarding({
  onComplete,
  signedIn = false,
}: {
  onComplete: (destination: "signup" | "signin") => void;
  signedIn?: boolean;
}) {
  const [step, setStep] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const firstRender = useRef(true);
  const current = steps[step];
  const finalStep = step === steps.length - 1;

  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    heading.current?.focus();
  }, [step]);

  return (
    <div
      className={`onboarding onboarding-step-${step + 1}`}
      data-step={step + 1}
    >
      <header className="onboarding-topbar">
        <div className="onboarding-brand">
          <BrandMark />
          <span>
            ThinkMedia<span className="brand-dot">.</span>
          </span>
        </div>
        <button
          className="onboarding-skip text-button"
          type="button"
          onClick={() => onComplete("signin")}
        >
          Skip introduction
        </button>
      </header>
      <main className="onboarding-layout" id="onboarding-main">
        <div className="onboarding-visual" aria-hidden="true">
          <Artwork kind={current.artwork} className="onboarding-art" priority />
          <div className="onboarding-visual-tabs">
            {steps.map((item, index) => (
              <span
                key={item.label}
                className={`onboarding-visual-tab ${index === step ? "active" : ""}`}
              >
                <ThinkIcon name={item.icon} size={28} />
                <span>{item.label}</span>
              </span>
            ))}
          </div>
        </div>
        <section className="onboarding-copy" aria-labelledby="onboarding-title">
          <div className="onboarding-step-icon" aria-hidden="true">
            <ThinkIcon name={current.icon} size={32} />
          </div>
          <h1 id="onboarding-title" ref={heading} tabIndex={-1}>
            {current.title}
          </h1>
          <p className="onboarding-description">{current.description}</p>
          <p className="onboarding-note">{current.note}</p>
          <div className="onboarding-progress">
            <ol
              className="onboarding-pagination"
              aria-label="Introduction steps"
            >
              {steps.map((item, index) => (
                <li key={item.label}>
                  <button
                    type="button"
                    aria-label={`${index + 1}. ${item.label}`}
                    aria-current={index === step ? "step" : undefined}
                    onClick={() => setStep(index)}
                  >
                    <span aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ol>
            <span className="onboarding-step-count">
              {step + 1} of {steps.length}
            </span>
          </div>
          <div className="onboarding-actions">
            {step > 0 && (
              <button
                type="button"
                className="secondary onboarding-back"
                onClick={() => setStep(step - 1)}
              >
                Back
              </button>
            )}
            <button
              type="button"
              className="primary onboarding-next"
              onClick={() =>
                finalStep
                  ? onComplete(signedIn ? "signin" : "signup")
                  : setStep(step + 1)
              }
            >
              {finalStep
                ? signedIn
                  ? "Go to workspace"
                  : "Create account"
                : "Next"}
              <svg
                viewBox="0 0 24 24"
                width="20"
                height="20"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
                focusable="false"
              >
                <path d="M4 12h15m-6-6 6 6-6 6" />
              </svg>
            </button>
          </div>
          {!signedIn && (
            <p className="onboarding-signin">
              Already have an account?{" "}
              <button
                type="button"
                className="text-button"
                onClick={() => onComplete("signin")}
              >
                Sign in
              </button>
            </p>
          )}
        </section>
      </main>
    </div>
  );
}

export default Onboarding;
