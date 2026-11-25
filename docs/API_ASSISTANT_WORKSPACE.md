# Assistant workspace actions

FR02–04/08/10–11, NFR02–06/09/11. This prototype extension retains the fixed
proposal's read-only boundary for application decisions and privileged approvals.
Groq `openai/gpt-oss-20b` proposes one bounded local function call. The backend
validates the tool name and arguments, enforces the signed-in role, and executes
only registered services. It does not execute model-supplied code or URLs.

| Capability | Roles | Result |
| --- | --- | --- |
| Grounded guidance, lesson and opportunity search | All | Approved sources and public result cards |
| Greetings, acknowledgements and clarification | All | Conversational reply; no application action or source claim |
| Navigate | All | A permitted internal page; no arbitrary URL |
| Suggestions | Student | Locally generated recommendations |
| Save a resource | Student | Preview, then explicit confirmation |
| Update own profile | Student, instructor, company | Preview of permitted fields, then confirmation |
| Create lesson or skill draft | Instructor | Preview, then confirmation; normal review still required |
| Create listing draft | Verified company | Preview, then confirmation; publication stays in the company portal |
| Verification, publication, applications and hiring decisions | Authorized roles via existing screens | Navigation and explanation only |

`POST /api/v1/assistant` keeps its existing guidance contract when `workspace`
is omitted. With `workspace: true` and a bounded `page`, it may also return
`results`, `navigation`, or a `proposal` with human-readable changes. Tool outputs
are rendered locally, never sent back to the model. Private profiles,
applications and PDFs are excluded from provider context. A user should not
include sensitive records in the question itself.

`POST /api/v1/assistant/actions/{id}/confirm` and `/cancel` require authentication
and CSRF. Proposals are bound to actor and session, expire after ten minutes, and
are locked when consumed. Confirmation revalidates the role, resource state and
profile preconditions. The effect and its execution record commit together.
Expired, cancelled, replayed and cross-session proposals cannot execute.

Only approved public excerpts, the question, bounded preceding questions, the
current page name and allowed function definitions reach the provider. Retrieved
content and model output remain untrusted. Existing throttling and the shared
provider attempt budget also apply to planning. `APP_ASSISTANT_TOOLS_ENABLED=false`
disables workspace actions while retaining the configured guidance mode.

Groq tool calling is requested separately from strict structured-answer mode;
the two modes are not combined. Provider errors leave normal application
workflows available. Retrieval-only development remains explicitly labeled and
does not claim to be a live tool-using model.

November 25 conversation correction: standalone English greetings and thanks
receive a local, throttled reply before model planning. These replies use
`mode: "conversation"` and do not consume provider calls. A greeting with an
explicit task still reaches the planner. Model-generated clarification and
available-help replies use a bounded, read-only `reply` function. The UI labels
these as Conversation and omits unrelated citation and satisfaction controls.
Factual preparation guidance retains its citation and uncertainty checks.

The planner receives earlier questions as completed context in a separate user
message, followed by the latest question as the final user message. Earlier
requests cannot serve as fresh authorization to repeat an action. Role checks
and write confirmation remain unchanged.
