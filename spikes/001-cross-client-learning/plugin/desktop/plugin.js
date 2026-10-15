/* Disposable personal-use spike. No model calls or tracking on mount.
 * The renderer below is intentionally duplicated from dashboard/dist/index.js.
 * Only the official disk-plugin imports are used; no JSX/build step.
 */
import * as React from "react";
import { Button, Input, Textarea, host, useValue, ROUTES_AREA, SIDEBAR_NAV_AREA } from "@hermes/plugin-sdk";

  function createLearningPage(React, ui, request) {
    const h = React.createElement;
    const { useState, useRef, useEffect } = React;
    const Button = ui.Button || "button";
    const Input = ui.Input || "input";
    const Textarea = ui.Textarea || "textarea";
    const text = (value, fallback = "") => typeof value === "string" ? value : fallback;
    const styles = {
      page: { maxWidth: "900px", margin: "0 auto", padding: "20px", display: "grid", gap: "16px", overflow: "auto", height: "100%", alignContent: "start", color: "var(--color-foreground, var(--ui-text-primary))", fontSize: "14px", lineHeight: 1.5 },
      card: { border: "1px solid var(--color-border, var(--ui-stroke-secondary))", borderRadius: "8px", padding: "14px", display: "grid", gap: "10px", minWidth: 0 },
      row: { display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" },
      muted: { color: "var(--color-muted-foreground, var(--ui-text-secondary))", fontSize: "13px" },
      field: { width: "100%", minWidth: 0, padding: "8px", color: "inherit", background: "var(--color-card, var(--ui-bg-primary))", border: "1px solid var(--color-border, var(--ui-stroke-secondary))", borderRadius: "5px", font: "inherit" },
      wrap: { overflowWrap: "anywhere", whiteSpace: "pre-wrap" },
      heading: { margin: 0, fontSize: "18px", fontWeight: 600 }
    };
    function checkLesson(value) {
      if (!value || typeof value.title !== "string" || !Array.isArray(value.participants) ||
          value.participants.length < 1 || value.participants.length > 12 ||
          !Array.isArray(value.steps) || value.steps.length < 1 || value.steps.length > 40) {
        throw new Error("Invalid lesson: expected a title, 1–12 participants and 1–40 steps.");
      }
      const ids = new Set();
      for (const item of value.participants) {
        if (!item || typeof item.id !== "string" || !item.id || ids.has(item.id) || typeof item.label !== "string") {
          throw new Error("Invalid lesson participant.");
        }
        ids.add(item.id);
      }
      for (const step of value.steps) {
        if (!step || !ids.has(step.from) || !ids.has(step.to) || typeof step.label !== "string") {
          throw new Error("Invalid lesson step: participant reference or label is missing.");
        }
      }
      return value;
    }
    function checkState(value) {
      if (!value || value.api_version !== 1 || typeof value.store_id !== "string" ||
          !Array.isArray(value.contexts) || !Array.isArray(value.attempts)) {
        throw new Error("Unsupported learning state. Expected API version 1.");
      }
      for (const ctx of value.contexts) checkContext(ctx);
      return value;
    }
    function checkContext(ctx) {
      if (!ctx || typeof ctx.id !== "string" || !ctx.id || typeof ctx.label !== "string" ||
          typeof ctx.run_id !== "string" || !ctx.run_id || ![true, false, 0, 1].includes(ctx.active)) {
        throw new Error("Invalid server-issued learning context.");
      }
      return ctx;
    }
    function assistance(value) {
      if (value == null) return "Not supplied";
      return typeof value === "string" ? value : JSON.stringify(value);
    }
    function Diagram({ lesson, index, marker }) {
      const participants = lesson.participants;
      const step = lesson.steps[index];
      const width = Math.max(400, participants.length * 150);
      const x = id => 75 + participants.findIndex(item => item.id === id) * 150;
      const from = x(step.from), to = x(step.to);
      const self = from === to;
      const description = `${text(step.label)}: ${text(participants.find(p => p.id === step.from)?.label)} to ${text(participants.find(p => p.id === step.to)?.label)}`;
      return h("div", { style: { overflowX: "auto" } },
        h("svg", { viewBox: `0 0 ${width} 185`, role: "img", "aria-label": description, style: { width: "100%", minWidth: `${width}px`, height: "185px", color: "var(--color-primary, var(--ui-accent))" } },
          h("defs", null, h("marker", { id: marker, viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" }, h("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "currentColor" }))),
          participants.map(item => h("g", { key: item.id },
            h("text", { x: x(item.id), y: 24, textAnchor: "middle", fill: "currentColor", fontSize: 12 }, item.label),
            h("line", { x1: x(item.id), y1: 40, x2: x(item.id), y2: 175, stroke: "currentColor", strokeDasharray: "4 5", opacity: 0.45 }))),
          h("path", { d: self ? `M ${from} 85 h 48 v 45 h -48` : `M ${from} 105 H ${to}`, fill: "none", stroke: "currentColor", strokeWidth: 2, markerEnd: `url(#${marker})` }),
          h("text", { x: self ? from + 55 : (from + to) / 2, y: 75, textAnchor: self ? "start" : "middle", fill: "currentColor", fontSize: 12 }, text(step.label))));
    }

    return function LearningPage() {
      const [model, setModel] = useState({ lesson: null, state: null, selected: null, step: 0, label: "", answer: "", hint: "", result: null, pending: null, pendingStoreId: null, busy: true, error: "", notice: "" });
      const live = useRef(model);
      const alive = useRef(true);
      const markerRef = useRef(null);
      // IDs are presentation-only, never learning context or submission IDs.
      if (!markerRef.current) markerRef.current = `learning-arrow-${Math.random().toString(36).slice(2)}`;
      const prefix = markerRef.current;
      function update(patch) {
        if (!alive.current) return;
        live.current = { ...live.current, ...patch };
        setModel(live.current);
      }
      async function refreshState() {
        const state = checkState(await request("/state"));
        if (!alive.current) return;
        const current = live.current;
        const changedStore = current.state && current.state.store_id !== state.store_id;
        const selected = !changedStore && current.selected && state.contexts.find(ctx => ctx.id === current.selected.id && ctx.active);
        const patch = { state };
        if (current.selected) {
          patch.selected = selected || null;
          if (!selected || selected.run_id !== current.selected.run_id) {
            Object.assign(patch, { hint: "", result: null, notice: changedStore ? "Backend store changed. Explicitly start or resume before writing." : !selected ? "Selected context is no longer active. Tracking is off in this view." : "Server run changed. Current run refreshed; any uncertain submission keeps its original run ID and answer." });
          }
        }
        // Selection follows the current server run; a retry payload does not.
        // Only exact evidence from its original store resolves uncertain delivery.
        const pending = current.pending;
        const committed = pending && current.pendingStoreId === state.store_id && state.attempts.find(item =>
          typeof item.id === "string" && item.id && item.context_id === pending.context_id && item.run_id === pending.run_id && item.answer === pending.answer);
        if (committed) Object.assign(patch, { pending: null, pendingStoreId: null, notice: "State readback confirms the exact submitted answer was committed." });
        update(patch);
      }
      async function load() {
        const results = await Promise.allSettled([request("/lesson").then(checkLesson), refreshState()]);
        if (!alive.current) return;
        update({ lesson: results[0].status === "fulfilled" ? results[0].value : null });
        const errors = results.filter(item => item.status === "rejected").map(item => text(item.reason?.message, String(item.reason)));
        if (errors.length) throw new Error(errors.join(" "));
      }
      async function action(work, refresh = true) {
        if (!alive.current || live.current.busy) return;
        update({ busy: true, error: "", notice: "" });
        try {
          await work();
          if (refresh && alive.current) await refreshState();
        } catch (error) {
          update({ error: text(error?.message, String(error)) });
          // A failed response can still mean the server committed. Read back,
          // but never retry a mutation automatically or rotate its run ID.
          if (refresh && alive.current) {
            try { await refreshState(); }
            catch (readError) { update({ error: `${live.current.error} State refresh also failed: ${text(readError?.message, String(readError))}` }); }
          }
        } finally { update({ busy: false }); }
      }
      useEffect(() => {
        alive.current = true;
        load().catch(error => update({ error: text(error?.message, String(error)) })).finally(() => update({ busy: false }));
        return () => { alive.current = false; };
      }, []);
      function currentContext() {
        const value = live.current;
        if (!value.selected || !value.state?.contexts.some(ctx => ctx.id === value.selected.id && ctx.active)) {
          throw new Error("Start or explicitly resume an active context before writing.");
        }
        return value.selected;
      }
      function select(ctx) {
        const keepPending = live.current.pending && live.current.pendingStoreId === live.current.state?.store_id && live.current.pending.context_id === ctx.id;
        update({ selected: ctx, answer: keepPending ? live.current.pending.answer : "", hint: "", result: null, pending: keepPending ? live.current.pending : null, pendingStoreId: keepPending ? live.current.pendingStoreId : null, notice: "Tracked context selected. Hints and submitted answers are recorded; reading and step navigation are not." });
      }
      function start() {
        return action(async () => {
          const ctx = checkContext(await request("/start", { label: live.current.label.trim() || "Learning spike" }));
          if (!ctx.active) throw new Error("Server returned an inactive context.");
          select(ctx);
        });
      }
      function resume(id) {
        return action(async () => {
          await refreshState();
          const ctx = live.current.state?.contexts.find(item => item.id === id && item.active);
          if (!ctx) throw new Error("This context is no longer active. Start a new tracked context.");
          select(ctx);
        }, false);
      }
      function submit() {
        return action(async () => {
          const ctx = currentContext();
          const pending = live.current.pending || { context_id: ctx.id, run_id: ctx.run_id, answer: live.current.answer };
          if (live.current.pending && (live.current.pendingStoreId !== live.current.state.store_id || pending.context_id !== ctx.id)) {
            throw new Error("This retry belongs to another store or context. Explicitly start or resume there, or choose New attempt to abandon it.");
          }
          if (!pending.answer.trim()) throw new Error("Enter an optional prediction before submitting.");
          update({ pending, pendingStoreId: live.current.state.store_id });
          const result = await request("/attempt", pending);
          if (!result?.attempt || result.attempt.context_id !== pending.context_id || result.attempt.run_id !== pending.run_id || result.attempt.answer !== pending.answer || typeof result.attempt.id !== "string" || !result.attempt.id) {
            throw new Error("Invalid attempt response. Keep this run ID and retry or refresh.");
          }
          update({ result: ctx.run_id === pending.run_id ? result : null, pending: null, pendingStoreId: null, notice: result.duplicate ? "Existing attempt returned for this run; no duplicate created." : "Server acknowledged the attempt. Refreshing committed state." });
        });
      }
      function newAttempt() {
        return action(async () => {
          const ctx = currentContext();
          const result = await request("/runs", { context_id: ctx.id });
          if (typeof result?.run_id !== "string" || !result.run_id) throw new Error("Invalid new-attempt response.");
          update({ selected: { ...ctx, run_id: result.run_id }, pending: null, pendingStoreId: null, result: null, answer: "", hint: "", notice: "New run issued. An intentional repeat can now be submitted." });
        });
      }
      function hint() {
        return action(async () => {
          const result = await request("/hint", { context_id: currentContext().id });
          if (typeof result?.hint !== "string") throw new Error("Invalid hint response.");
          update({ hint: result.hint, notice: "Server acknowledged the hint and its assistance record. Refreshing state." });
        });
      }
      function leave() {
        return action(async () => {
          const ctx = currentContext();
          // Revoke local selection immediately even if the server rejects exit.
          update({ selected: null, pending: null, pendingStoreId: null, result: null, hint: "" });
          const result = await request("/leave", { context_id: ctx.id });
          if (result?.ok !== true) throw new Error("Exit was not acknowledged. Refresh to inspect server context status.");
          update({ notice: "Left tracked learning. Committed records remain; this view is read-only." });
        });
      }
      const { lesson, state, selected, busy } = model;
      const index = lesson ? Math.min(model.step, lesson.steps.length - 1) : 0;
      const saved = selected && state?.attempts.find(item => item.context_id === selected.id && item.run_id === selected.run_id);
      const locked = !model.pending && (!!saved || !!model.result);
      const button = (label, onClick, disabled = false) => h(Button, { type: "button", onClick, disabled: busy || disabled, style: { whiteSpace: "normal" } }, label);
      const heading = value => h("h2", { style: styles.heading }, value);
      const attemptView = (attempt, key) => h("li", { key, style: { ...styles.card, marginBottom: "8px" } },
        h("strong", null, text(attempt.status, "Unknown status").replaceAll("_", " ")),
        h("div", { style: styles.wrap }, text(attempt.answer, "No answer returned")),
        h("small", { style: { ...styles.muted, overflowWrap: "anywhere" } }, `Context: ${text(attempt.context_id)} · Run: ${text(attempt.run_id)}`),
        h("div", { style: { ...styles.muted, ...styles.wrap } }, `Assistance: ${assistance(attempt.assistance)}`));
      return h("main", { style: styles.page, "aria-label": "Learning spike", "aria-busy": busy },
        h("header", null, h("h1", { style: { ...styles.heading, fontSize: "24px" } }, "Learning spike"),
          h("p", { style: styles.muted }, "Disposable personal-use spike. Reading is untracked. Answering is optional. No model is called; submissions await assessment.")),
        h("div", { style: styles.row }, button(busy ? "Loading…" : "Refresh lesson and state", () => action(load, false)),
          h("span", { role: "status", style: styles.muted }, selected ? `Selected for writes: ${selected.label}` : "Read-only · no context selected")),
        model.error && h("div", { role: "alert", style: styles.card }, h("strong", null, "Request failed"), h("div", { style: styles.wrap }, model.error), h("small", null, "No automatic mutation retry. Refresh or retry explicitly; failed submissions keep their original run ID and answer.")),
        model.notice && h("p", { role: "status", style: styles.wrap }, model.notice),
        lesson && h("section", { style: styles.card, "aria-label": "Lesson and sequence" },
          heading(lesson.title), h("p", { style: { margin: 0 } }, text(lesson.objective, "No objective supplied.")),
          h("details", null, h("summary", null, text(lesson.source?.title, "Source excerpt")),
            h("p", { style: styles.wrap }, text(lesson.source?.text, "No source excerpt supplied.").slice(0, 1400))),
          h(Diagram, { lesson, index, marker: prefix }),
          h("div", { style: styles.row }, button("Previous step", () => update({ step: Math.max(0, live.current.step - 1) }), index === 0),
            h("span", { role: "status", "aria-live": "polite" }, `Step ${index + 1} of ${lesson.steps.length}`),
            button("Next step", () => update({ step: Math.min(lesson.steps.length - 1, live.current.step + 1) }), index === lesson.steps.length - 1)),
          h("p", { style: styles.wrap, "aria-live": "polite" }, `${text(lesson.steps[index].label)} — ${text(lesson.steps[index].explanation, "No explanation supplied.")}`),
          h("details", null, h("summary", null, "Text alternative: all sequence steps"),
            h("ol", { style: { paddingLeft: "24px" } }, lesson.steps.map((step, i) => h("li", { key: i, "aria-current": i === index ? "step" : undefined, style: styles.wrap }, `${lesson.participants.find(p => p.id === step.from).label} → ${lesson.participants.find(p => p.id === step.to).label}: ${step.label}. ${text(step.explanation)}`))))),
        h("section", { style: styles.card, "aria-label": "Tracking controls" }, heading("Tracking is explicit"),
          h("p", { style: { ...styles.muted, margin: 0 } }, "Start creates a tracked context. Resume selects an already-active context for writes in this view; it does not reactivate an exited context. Context IDs act as write capabilities: do not share them. Nothing is selected automatically."),
          !selected && h("div", { style: styles.row },
            h("label", { htmlFor: `${prefix}-label` }, "Context label"),
            h(Input, { id: `${prefix}-label`, value: model.label, maxLength: 100, disabled: busy, style: { ...styles.field, maxWidth: "280px" }, onChange: event => update({ label: event.target.value }) }),
            button("Start tracked learning", start, !state)),
          selected && h("div", null, h("div", { style: styles.wrap }, `Context: ${selected.label} · Run: ${selected.run_id}`),
            h("div", { style: styles.row }, button("Show hint (records assistance)", hint), button("New attempt (new run ID)", newAttempt), button("Leave tracked learning", leave))),
          model.hint && h("p", { style: styles.wrap }, model.hint),
          state && h("div", null, h("small", { style: { ...styles.muted, overflowWrap: "anywhere" } }, `Backend store: ${state.store_id} · API ${state.api_version} · refresh manually for other-client changes`),
            h("ul", { style: { paddingLeft: "20px" } }, state.contexts.map(ctx => h("li", { key: ctx.id, style: { marginTop: "8px", overflowWrap: "anywhere" } },
              `${ctx.label} · ${ctx.active ? "active on server" : "exited"} `,
              Boolean(ctx.active) && !selected && button(`Resume for writes: ${ctx.label}`, () => resume(ctx.id)),
              selected?.id === ctx.id && h("strong", null, " · selected here"))))),
          state && state.contexts.length === 0 && h("p", { style: styles.muted }, "No tracked contexts yet.")),
        lesson && h("section", { style: styles.card, "aria-label": "Optional prediction" }, heading("Optional prediction"),
          h("p", { style: styles.wrap }, text(lesson.prompt, "No prediction prompt supplied.")),
          h("label", { htmlFor: `${prefix}-answer` }, "Private unsubmitted draft — stays only in this mounted view; lost on reload or context change."),
          h(Textarea, { id: `${prefix}-answer`, value: model.answer, rows: 4, maxLength: 8000, disabled: busy || !!model.pending || locked, style: { ...styles.field, resize: "vertical" }, onChange: event => update({ answer: event.target.value }) }),
          h("div", { style: styles.row }, button(model.pending ? "Retry same submission" : "Submit prediction", submit, !selected || !model.answer.trim() || locked),
            !selected && h("small", { style: styles.muted }, "Start or explicitly Resume to submit; reading never requires an answer.")),
          model.pending && h("p", { style: styles.muted }, `Delivery uncertain. Retry preserves run ${model.pending.run_id} and the exact answer. New attempt explicitly abandons this retry payload.`),
          locked && h("p", { role: "status", style: styles.muted }, saved ? `Committed attempt: ${text(saved.status).replaceAll("_", " ")}. Use New attempt for an intentional repeat.` : "Server acknowledged the attempt; committed-state refresh is still needed."),
          model.result?.criteria && Array.isArray(model.result.criteria) && h("details", null, h("summary", null, "Assessment criteria"), h("ul", null, model.result.criteria.map((criterion, i) => h("li", { key: i }, text(criterion))))),
          h("small", { style: styles.muted }, "No automated grade or model feedback. Continue in chat for review of a committed pending attempt.")),
        h("section", { style: styles.card, "aria-label": "Committed attempts" }, heading("Committed attempts · shared backend"),
          !state && h("p", null, "State unavailable. Use Refresh to retry."),
          state && state.attempts.length === 0 && h("p", { style: styles.muted }, "No committed attempts. Reading alone does not create one."),
          state && h("ul", { style: { listStyle: "none", padding: 0, margin: 0 } }, state.attempts.slice(-20).reverse().map((item, i) => attemptView(item, text(item.id, String(i))))),
          state && state.attempts.length > 20 && h("small", { style: styles.muted }, "Showing the most recent 20 returned attempts.")));
    };
  }


export default {
  id: "hermes-learning-spike",
  name: "Learning spike (disposable)",
  defaultEnabled: false,
  register(ctx) {
    const request = (path, body) => ctx.rest(path, body === undefined
      ? { method: "GET" }
      : { method: "POST", body });
    const Page = createLearningPage(React, { Button, Input, Textarea }, request);
    function ScopedPage() {
      // Profile/connection transitions drop write selection and local drafts.
      // The backend also validates context capabilities for every mutation.
      const profile = useValue(host.state.profile);
      const gateway = useValue(host.state.gateway);
      return React.createElement(Page, { key: `${profile}:${gateway}` });
    }
    ctx.register({
      id: "learning-spike", area: ROUTES_AREA,
      data: { path: "/learning-spike" },
      render: () => React.createElement(ScopedPage)
    });
    ctx.register({
      id: "learning-spike-nav", area: SIDEBAR_NAV_AREA,
      data: { path: "/learning-spike", label: "Learning spike", codicon: "book" }
    });
  }
};
