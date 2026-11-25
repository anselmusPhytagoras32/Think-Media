// FR10/12, W07; NFR03/05/09/11: bounded, private page-memory guidance.
import { type FormEvent, useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  BookOpen,
  BriefcaseBusiness,
  ChevronDown,
  FileText,
  LoaderCircle,
  MessagesSquare,
  Send,
  ShieldCheck,
  ThumbsUp,
  Trash2,
  X,
} from "lucide-react";
import { api } from "./api";
import { Artwork } from "./artwork";
import { BrandMark } from "./brand";

type GuidanceAnswer = {
  answer: string;
  sources: { id: string; title: string }[];
  uncertainty: string | boolean;
  mode: string;
  results?: {
    id: string;
    title: string;
    summary: string;
    href: string;
    kind: string;
  }[];
  navigation?: { label: string; href: string };
  proposal?: {
    id: string;
    label: string;
    changes: Record<string, unknown>;
    expires_at: string;
  };
};
type Exchange = {
  id: number;
  question: string;
  answer?: GuidanceAnswer;
  error?: string;
  actionResult?: { answer: string; href?: string };
  actionError?: string;
};

function workspaceLink(value: string) {
  return /^#\/(overview|profile|learning|opportunities|applications|suggestions|authoring|review|verification|content|learning-review|reports|audit)(\/[0-9a-f-]{36})?$/.test(
    value,
  );
}

function changeText(value: unknown): string {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value))
    return value.every((item) => typeof item === "string")
      ? value.join(", ")
      : value.map(changeText).join("\n\n");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(([key, item]) => `${key.replace(/_/g, " ")}: ${changeText(item)}`)
      .join("\n");
  return String(value ?? "");
}
type Source = { id: string; title: string; body: string };
const starters = [
  {
    label: "Interview prep",
    question: "How can I prepare for an OJT interview?",
    icon: MessagesSquare,
  },
  {
    label: "Resume tips",
    question: "What should I include in my OJT resume?",
    icon: FileText,
  },
  {
    label: "Workplace skills",
    question: "What workplace skills should I practice before my OJT?",
    icon: BriefcaseBusiness,
  },
];

function Satisfaction() {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/feedback/csat", "POST", { rating: Number(value) });
      setSaved(true);
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="guidance-feedback">
      <summary>
        <ThumbsUp size={15} aria-hidden="true" /> Rate this guidance{" "}
        <ChevronDown size={14} aria-hidden="true" />
      </summary>
      <form className="satisfaction-form" onSubmit={submit}>
        <p>Optional. Your rating does not affect applications.</p>
        <label htmlFor="guidance-satisfaction">
          Helpfulness rating (optional)
        </label>
        <div className="guidance-rating-controls">
          <select
            id="guidance-satisfaction"
            required
            value={value}
            onChange={(event) => {
              setValue(event.target.value);
              setSaved(false);
            }}
          >
            <option value="">Choose a rating</option>
            <option value="1">1 · Very unhelpful</option>
            <option value="2">2 · Unhelpful</option>
            <option value="3">3 · Neutral</option>
            <option value="4">4 · Helpful</option>
            <option value="5">5 · Very helpful</option>
          </select>
          <button className="secondary" disabled={busy || !value}>
            Share satisfaction rating
          </button>
        </div>
        {saved && (
          <p className="rating-saved" role="status">
            Thank you. Your satisfaction rating was saved.
          </p>
        )}
        {error && (
          <p className="field-error" role="alert">
            {error}
          </p>
        )}
      </form>
    </details>
  );
}

export function Assistant({ embedded = false }: { embedded?: boolean }) {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [source, setSource] = useState<{
    content: Source;
    exchangeId: number;
  } | null>(null);
  const [sourceError, setSourceError] = useState("");
  const [sourceBusy, setSourceBusy] = useState("");
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const [workspacePrompts, setWorkspacePrompts] = useState<
    { label: string; question: string }[]
  >([]);
  const nextExchange = useRef(0);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const scrollArea = useRef<HTMLDivElement>(null);
  const sourceHeading = useRef<HTMLHeadingElement>(null);
  const sourceOpener = useRef<HTMLButtonElement | null>(null);
  const stickToEnd = useRef(true);

  useEffect(() => {
    let current = true;
    api<{
      actions_available: boolean;
      prompts: { label: string; question: string }[];
    }>("/assistant/capabilities")
      .then((data) => {
        if (current && data.actions_available)
          setWorkspacePrompts(data.prompts);
      })
      .catch(() => {});
    return () => {
      current = false;
    };
  }, []);

  useEffect(() => {
    if (scrollArea.current && stickToEnd.current)
      scrollArea.current.scrollTop = scrollArea.current.scrollHeight;
  }, [exchanges]);
  useEffect(() => {
    if (source) sourceHeading.current?.focus();
  }, [source]);
  useEffect(() => {
    const input = textarea.current;
    if (!input) return;
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
  }, [question]);

  async function ask(event?: FormEvent, retry?: Exchange) {
    event?.preventDefault();
    const submittedQuestion = retry?.question || question.trim();
    if (!submittedQuestion || busy) return;
    const id = retry?.id ?? ++nextExchange.current;
    const exchange: Exchange = { id, question: submittedQuestion };
    stickToEnd.current = true;
    setExchanges((old) =>
      retry
        ? old.map((item) => (item.id === id ? exchange : item))
        : [...old, exchange].slice(-10),
    );
    setBusy(true);
    setSource(null);
    setSourceError("");
    setAnnouncement("Checking approved resources…");
    try {
      const answer = await api<GuidanceAnswer>("/assistant", "POST", {
        question: submittedQuestion,
        workspace: true,
        page:
          window.location.hash.replace(/^#\/?/, "").split(/[/?]/)[0] ||
          "overview",
        resource_id: /^#\/learning\/[0-9a-f-]{36}$/.test(window.location.hash)
          ? window.location.hash.split("/")[2]
          : undefined,
        previous_questions: exchanges
          .filter((item) => item.answer && (!retry || item.id < retry.id))
          .slice(-3)
          .map((item) => item.question.slice(0, 1000)),
      });
      setExchanges((old) =>
        old.map((item) => (item.id === id ? { ...item, answer } : item)),
      );
      setAnnouncement(
        answer.mode === "conversation"
          ? "Reply is ready."
          : answer.proposal
            ? "A proposed change is ready. Review it before confirming."
            : answer.results?.length || answer.navigation
              ? "The response is ready. Read it in the conversation."
              : "Guidance is ready. Read the response and its sources in the conversation.",
      );
      if (!retry)
        setQuestion((current) =>
          current.trim() === submittedQuestion ? "" : current,
        );
    } catch (failure) {
      setExchanges((old) =>
        old.map((item) =>
          item.id === id
            ? { ...item, error: (failure as Error).message }
            : item,
        ),
      );
      setAnnouncement("Guidance is unavailable. You can retry this question.");
    } finally {
      setBusy(false);
    }
  }

  async function handleProposal(
    exchange: Exchange,
    operation: "confirm" | "cancel",
  ) {
    if (busy || !exchange.answer?.proposal || exchange.actionResult) return;
    setBusy(true);
    setExchanges((old) =>
      old.map((item) =>
        item.id === exchange.id ? { ...item, actionError: undefined } : item,
      ),
    );
    try {
      const actionResult = await api<{ answer: string; href?: string }>(
        `/assistant/actions/${exchange.answer.proposal.id}/${operation}`,
        "POST",
        {},
      );
      setExchanges((old) =>
        old.map((item) =>
          item.id === exchange.id ? { ...item, actionResult } : item,
        ),
      );
      setAnnouncement(actionResult.answer);
    } catch (failure) {
      setExchanges((old) =>
        old.map((item) =>
          item.id === exchange.id
            ? { ...item, actionError: (failure as Error).message }
            : item,
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {!embedded && (
        <header className="page-heading">
          <div>
            <h1>
              {workspacePrompts.length
                ? "ThinkMedia assistant"
                : "OJT preparation guidance"}
            </h1>
            <p>
              {workspacePrompts.length
                ? "Find resources and get help with your workspace."
                : "A little preparation for your next step."}
            </p>
          </div>
        </header>
      )}
      <section
        className={`assistant-panel guidance-chat ${embedded ? "guidance-chat-embedded" : "guidance-chat-page"}`}
        aria-label={
          workspacePrompts.length ? "ThinkMedia assistant" : "Ask about OJT"
        }
      >
        <div className="guidance-conversation-tools">
          <span>
            <BookOpen size={15} aria-hidden="true" />{" "}
            {workspacePrompts.length
              ? "Workspace help and approved resources"
              : "Approved resources"}
          </span>
          {exchanges.length > 0 ? (
            <button
              type="button"
              className="guidance-clear"
              aria-label="Clear conversation"
              disabled={busy || !!sourceBusy}
              onClick={() => {
                setExchanges([]);
                setSource(null);
                setSourceError("");
                setAnnouncement("Conversation cleared.");
                textarea.current?.focus();
              }}
            >
              <Trash2 size={15} aria-hidden="true" /> Clear
            </button>
          ) : (
            <span
              className="guidance-memory"
              title="The latest 10 exchanges stay in this page's memory until you leave or clear them."
            >
              This page only
            </span>
          )}
        </div>
        <div
          className="guidance-scroll"
          ref={scrollArea}
          onScroll={() => {
            const area = scrollArea.current;
            if (area)
              stickToEnd.current =
                area.scrollHeight - area.scrollTop - area.clientHeight < 60;
          }}
        >
          {exchanges.length === 0 && (
            <div className="guidance-welcome">
              <div className="guidance-welcome-art">
                <Artwork kind="learning" priority />
              </div>
              <h2>
                {workspacePrompts.length ? (
                  <>
                    What can I help
                    <br />
                    you do?
                  </>
                ) : (
                  <>
                    Let’s get you
                    <br />
                    OJT-ready.
                  </>
                )}
              </h2>
              <p>
                {workspacePrompts.length
                  ? "Ask for help or choose a task below. Review proposed changes before saving."
                  : "Explore resume tips, interview prep and skills for your first day."}
              </p>
              {workspacePrompts.length > 0 && (
                <div
                  className="guidance-workspace-prompts"
                  aria-label="Workspace help"
                >
                  <p>
                    Find content, open your workspace, or prepare a change to
                    review.
                  </p>
                  {workspacePrompts.map((prompt) => (
                    <button
                      type="button"
                      className="text-button"
                      key={prompt.label}
                      onClick={() => {
                        setQuestion(prompt.question);
                        textarea.current?.focus();
                      }}
                    >
                      {prompt.label}
                      <ArrowUpRight size={14} aria-hidden="true" />
                    </button>
                  ))}
                </div>
              )}
              <div
                className="guidance-starters"
                aria-label="Suggested questions"
              >
                {starters.map(({ label, question: starter, icon: Icon }) => (
                  <button
                    key={label}
                    type="button"
                    onClick={() => {
                      setQuestion(starter);
                      textarea.current?.focus();
                    }}
                  >
                    <Icon size={18} aria-hidden="true" />
                    <span>{label}</span>
                    <ArrowUpRight size={16} aria-hidden="true" />
                  </button>
                ))}
              </div>
            </div>
          )}
          <section
            aria-label="Guidance conversation"
            className="guidance-conversation"
            aria-busy={busy}
          >
            {exchanges.map((exchange, index) => (
              <article
                className="assistant-answer guidance-exchange"
                key={exchange.id}
                aria-labelledby={`exchange-${exchange.id}`}
              >
                <div className="guidance-question">
                  <h2 className="sr-only" id={`exchange-${exchange.id}`}>
                    Your question
                  </h2>
                  <p className="preserve-lines">{exchange.question}</p>
                </div>
                <div className="guidance-reply">
                  <BrandMark size={27} className="guidance-avatar" />
                  <div className="guidance-reply-content">
                    {!exchange.answer && !exchange.error && (
                      <div className="guidance-thinking">
                        <LoaderCircle size={16} aria-hidden="true" />
                        <span>Checking approved resources…</span>
                      </div>
                    )}
                    {exchange.error && (
                      <div className="assistant-recovery">
                        <p role="alert">{exchange.error}</p>
                        <p>
                          Your applications and opportunities remain available.
                        </p>
                        <button
                          type="button"
                          className="secondary"
                          disabled={busy}
                          onClick={() => void ask(undefined, exchange)}
                        >
                          Try again
                        </button>
                      </div>
                    )}
                    {exchange.answer && (
                      <>
                        <span className="guidance-mode">
                          {exchange.answer.mode === "conversation"
                            ? "Conversation"
                            : exchange.answer.mode === "retrieval"
                              ? "Approved resource lookup"
                              : exchange.answer.proposal ||
                                  exchange.answer.navigation ||
                                  exchange.answer.results?.length
                                ? "Workspace help"
                                : "Grounded guidance"}
                        </span>
                        <h3 className="sr-only">
                          {exchange.answer.mode === "conversation"
                            ? "Assistant reply"
                            : "Guidance from approved resources"}
                        </h3>
                        <p className="preserve-lines guidance-answer-text">
                          {exchange.answer.answer}
                        </p>
                        {!!exchange.answer.results?.length && (
                          <ul className="guidance-workspace-results">
                            {exchange.answer.results
                              .filter((result) => workspaceLink(result.href))
                              .map((result) => (
                                <li key={result.id}>
                                  <a href={result.href}>
                                    {result.title}
                                    <ArrowUpRight
                                      size={14}
                                      aria-hidden="true"
                                    />
                                  </a>
                                  <p>{result.summary}</p>
                                </li>
                              ))}
                          </ul>
                        )}
                        {exchange.answer.navigation &&
                          workspaceLink(exchange.answer.navigation.href) && (
                            <a
                              className="secondary"
                              href={exchange.answer.navigation.href}
                            >
                              {exchange.answer.navigation.label}
                              <ArrowUpRight size={14} aria-hidden="true" />
                            </a>
                          )}
                        {exchange.answer.proposal && (
                          <section
                            className="guidance-proposal"
                            aria-label="Proposed change"
                          >
                            <h4>{exchange.answer.proposal.label}</h4>
                            <dl>
                              {Object.entries(
                                exchange.answer.proposal.changes,
                              ).map(([label, value]) => (
                                <div key={label}>
                                  <dt>{label}</dt>
                                  <dd className="preserve-lines">
                                    {changeText(value).length > 500 ? (
                                      <details>
                                        <summary>
                                          Read proposed {label.toLowerCase()}
                                        </summary>
                                        <p className="preserve-lines">
                                          {changeText(value)}
                                        </p>
                                      </details>
                                    ) : (
                                      changeText(value)
                                    )}
                                  </dd>
                                </div>
                              ))}
                            </dl>
                            {exchange.actionResult ? (
                              <div role="status">
                                <p>{exchange.actionResult.answer}</p>
                                {exchange.actionResult.href &&
                                  workspaceLink(exchange.actionResult.href) && (
                                    <a
                                      className="secondary"
                                      href={exchange.actionResult.href}
                                    >
                                      Open updated page
                                      <ArrowUpRight
                                        size={14}
                                        aria-hidden="true"
                                      />
                                    </a>
                                  )}
                              </div>
                            ) : (
                              <>
                                <p>
                                  Confirm only if these details are correct.
                                  This preview expires after 10 minutes.
                                </p>
                                <div className="guidance-proposal-actions">
                                  <button
                                    type="button"
                                    className="primary"
                                    disabled={busy}
                                    onClick={() =>
                                      void handleProposal(exchange, "confirm")
                                    }
                                  >
                                    Confirm change
                                  </button>
                                  <button
                                    type="button"
                                    className="secondary"
                                    disabled={busy}
                                    onClick={() =>
                                      void handleProposal(exchange, "cancel")
                                    }
                                  >
                                    Cancel change
                                  </button>
                                </div>
                              </>
                            )}
                            {exchange.actionError && (
                              <p className="field-error" role="alert">
                                {exchange.actionError}
                              </p>
                            )}
                          </section>
                        )}
                        {exchange.answer.uncertainty && (
                          <p className="guidance-uncertainty">
                            {typeof exchange.answer.uncertainty === "string"
                              ? exchange.answer.uncertainty
                              : "The available resources may not fully answer your question."}
                          </p>
                        )}
                        {exchange.answer.mode !== "conversation" &&
                          ((!exchange.answer.proposal &&
                            !exchange.answer.navigation &&
                            !exchange.answer.results?.length) ||
                            exchange.answer.sources.length > 0) && (
                            <div className="guidance-sources">
                              <h4>Sources</h4>
                              {exchange.answer.sources.length ? (
                                exchange.answer.sources.map((citation) => (
                                  <button
                                    key={citation.id}
                                    type="button"
                                    disabled={!!sourceBusy}
                                    aria-expanded={
                                      source?.exchangeId === exchange.id &&
                                      source.content.id === citation.id
                                    }
                                    onClick={async (event) => {
                                      sourceOpener.current =
                                        event.currentTarget;
                                      setSourceBusy(citation.id);
                                      setSourceError("");
                                      try {
                                        setSource({
                                          content: await api<Source>(
                                            citation.id.startsWith("guide:")
                                              ? `/assistant/sources/${encodeURIComponent(citation.id.slice(6))}`
                                              : `/content/${citation.id}`,
                                          ),
                                          exchangeId: exchange.id,
                                        });
                                      } catch (failure) {
                                        setSourceError(
                                          (failure as Error).message,
                                        );
                                      } finally {
                                        setSourceBusy("");
                                      }
                                    }}
                                  >
                                    <BookOpen size={14} aria-hidden="true" />
                                    <span>
                                      {sourceBusy === citation.id
                                        ? "Opening resource…"
                                        : citation.title}
                                    </span>
                                    <ArrowUpRight
                                      size={14}
                                      aria-hidden="true"
                                    />
                                  </button>
                                ))
                              ) : (
                                <p>No matching approved sources were found.</p>
                              )}
                            </div>
                          )}
                        {source?.exchangeId === exchange.id && (
                          <section className="source-preview guidance-source-preview">
                            <div>
                              <h3 ref={sourceHeading} tabIndex={-1}>
                                {source.content.title}
                              </h3>
                              <button
                                type="button"
                                aria-label="Close source"
                                onClick={() => {
                                  setSource(null);
                                  sourceOpener.current?.focus();
                                }}
                              >
                                <X size={18} aria-hidden="true" />
                              </button>
                            </div>
                            <p className="preserve-lines">
                              {source.content.body}
                            </p>
                          </section>
                        )}
                        {exchange.answer.mode !== "conversation" &&
                          index === exchanges.length - 1 && (
                            <Satisfaction key={exchange.id} />
                          )}
                      </>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </section>
          {sourceError && (
            <p className="notice error" role="alert">
              {sourceError}
            </p>
          )}
        </div>
        <form className="guidance-composer" onSubmit={ask}>
          <label htmlFor="assistant-question">Your question</label>
          <div className="guidance-input-wrap">
            <textarea
              ref={textarea}
              id="assistant-question"
              required
              maxLength={2000}
              rows={2}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="What would you like help with?"
              aria-describedby="guidance-privacy"
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing &&
                  window.matchMedia("(pointer: fine)").matches
                ) {
                  event.preventDefault();
                  void ask();
                }
              }}
            />
            <button
              className="guidance-send"
              type="submit"
              aria-label={busy ? "Looking for guidance" : "Ask for guidance"}
              disabled={busy || !question.trim()}
            >
              <Send size={19} aria-hidden="true" />
            </button>
          </div>
          <p id="guidance-privacy">
            <ShieldCheck size={13} aria-hidden="true" /> Keep personal details
            out of questions.
          </p>
        </form>
        <p
          className="sr-only"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {announcement}
        </p>
      </section>
    </>
  );
}
