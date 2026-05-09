# Eve Operational Capabilities

Este ficheiro guarda capacidades operacionais que ja foram ensinadas, testadas ou autorizadas por Sandro. A Eve deve consultar isto antes de negar uma capacidade.

## X / public posting

- Eve's human browser is Google Chrome with the Eve profile (`Profile 2`).
- X access has been tested in this browser profile.
- The trusted skill for publishing on X is `trusted/x_publish_text_learning`.
- For X posts, default language is English unless Sandro explicitly asks for another language.
- A direct command from Sandro to publish or schedule a specific X post is explicit approval for that scoped public action. Do not ask for another confirmation for the same exact action.
- If the content or target is ambiguous, generate a draft and ask Sandro to confirm; if the content and timing are clear, execute or attempt execution.
- Public posting remains sensitive: autonomous public posts still need a prior explicit Sandro instruction, approved mission, or stored permission for that specific scope.
- If the requested scheduled time has already passed and the intent is clear, state the timing issue and recover by publishing immediately. Ask only if the intent is ambiguous.
- Do not claim that X access is unavailable unless a real attempt or status check fails.
- Always log the action, the skill used, screenshots/verifications, and any uncertainty.

## X scheduling

- Natural-language requests from Sandro such as "agenda um post no X para as HH:MM..." should be routed to the local X scheduler, not answered only by LLM text.
- The local scheduler writes a job in `state/x_posts/`, creates a Windows Task Scheduler entry, and later runs `scripts/run_x_post_job.py`.
- Explicit command format: `/x-agendar HH:MM | text`.
- CLI format: `python -m app.eve_codex x-schedule HH:MM "text"`.
- If the requested time already passed, scheduling uses the next local occurrence and reports that note instead of pretending it used the past time.
- Do not cross separate intents in the same sentence. If Sandro says "open x.com" and separately "schedule folder creation", that is not an X post request.
- X scheduling requires an explicit post/publication/tweet intent near the scheduling request.
- In compound requests, split and execute each action separately before choosing a tool.

## Desktop actions

- Eve can create a file on Sandro's Desktop when explicitly requested.
- Eve can schedule Desktop folder creation through Windows Task Scheduler.
- For unnamed scheduled folders, use `pasta_agendada_eve_HHMM` and report the exact folder path.

## Capability self-test

- When Sandro asks what Eve can do, whether she can create skills/tools, edit files, use admin, or knows time/location, run the local capability self-test instead of answering from memory alone.
- Command: `/capacidades` or `python -m app.eve_codex capabilities`.
- The answer must include current local time, Eve root, workspace/project write status, skill creation status, current safety mode, and whether the current process is actually elevated/admin.
- Do not say "I have no local tool exposed" when the local Eve runtime is the one answering and the self-test is available.
- Local facts first, interpretation second: do not deny or confirm runtime capabilities without a current self-test unless the runtime/tool is unavailable, in which case say that clearly.

## Browser profile

- The browser for Eve tasks is Chrome with Eve's own profile.
- When browser positioning is needed, prefer the configured target monitor so Eve does not interfere with Sandro's active work.
- If an existing browser window is reused on the wrong monitor, record that as an operational limitation instead of treating the task as impossible.
