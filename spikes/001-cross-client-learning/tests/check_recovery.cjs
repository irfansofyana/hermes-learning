/* Small dependency-free renderer checks; no browser, server, or React install. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
function renderer(file) {
  const code = fs.readFileSync(path.join(root, file), "utf8");
  return code.slice(code.indexOf("  function createLearningPage("), code.indexOf("\n  }", code.indexOf("  function createLearningPage(")) + 4);
}
const web = renderer("plugin/dashboard/dist/index.js");
assert.equal(renderer("plugin/desktop/plugin.js"), web, "Both adapters must use the same renderer");
const createPage = vm.runInNewContext(`${web}; createLearningPage`);
const lesson = JSON.parse(fs.readFileSync(path.join(root, "plugin/lesson.json"), "utf8"));
const copy = value => JSON.parse(JSON.stringify(value));

async function mounted() {
  const context = { id: "ctx-1", run_id: "run-1", label: "Fixture", active: 1, origin: "workspace_action" };
  const state = { api_version: 1, store_id: "store-1", contexts: [context], attempts: [] };
  let model, cursor, effect;
  const refs = [];
  const React = {
    createElement: (type, props, ...children) => ({ type, props: props || {}, children: children.flat(Infinity) }),
    useState(initial) { model ??= initial; return [model, next => { model = next; }]; },
    useRef(initial) { const slot = cursor++; return refs[slot] ??= { current: initial }; },
    useEffect(fn) { effect ??= fn; }
  };
  const calls = [];
  const page = {
    state, context, calls,
    onRuns() { context.run_id = "run-2"; return { run_id: "run-2" }; },
    onAttempt(body) {
      const attempt = { id: "attempt-1", ...copy(body), status: "awaiting_assessment", assistance: "none" };
      state.attempts.push(attempt);
      return { attempt, duplicate: false };
    }
  };
  async function request(route, body) {
    calls.push({ route, body: body === undefined ? undefined : copy(body) });
    if (route === "/state") return copy(state);
    if (route === "/lesson") return copy(lesson);
    if (route === "/runs") return page.onRuns(body);
    if (route === "/attempt") return page.onAttempt(body);
    throw Error(`Unexpected fixture request: ${route}`);
  }
  const Page = createPage(React, {}, request);
  function render() { cursor = 0; return Page(); }
  function nodes(node) { return node && typeof node === "object" ? [node, ...node.children.flatMap(nodes)] : []; }
  function strings(node) { return typeof node === "string" ? [node] : node && typeof node === "object" ? node.children.flatMap(strings) : []; }
  page.text = () => strings(render()).join("\n");
  page.button = label => nodes(render()).find(node => node.type === "button" && strings(node).join("") === label);
  page.click = async label => {
    const button = page.button(label);
    assert.ok(button, `Missing button: ${label}`);
    assert.equal(button.props.disabled, false, `Disabled button: ${label}`);
    await button.props.onClick();
  };
  page.answer = answer => {
    const input = nodes(render()).find(node => node.type === "textarea");
    assert.equal(input.props.disabled, false, "Answer should be editable");
    input.props.onChange({ target: { value: answer } });
  };
  render();
  effect();
  await new Promise(setImmediate);
  await page.click("Resume for writes: Fixture");
  return page;
}

const tests = [
  ["refresh reconciles another client's current run", async () => {
    const page = await mounted();
    page.context.run_id = "run-2";
    await page.click("Refresh lesson and state");
    page.answer("new run answer");
    await page.click("Submit prediction");
    assert.deepEqual(page.calls.find(call => call.route === "/attempt").body,
      { context_id: "ctx-1", run_id: "run-2", answer: "new run answer" });
  }],
  ["lost new-run response recovers through state refresh", async () => {
    const page = await mounted();
    page.onRuns = () => { page.context.run_id = "run-2"; throw Error("lost new-run response"); };
    await page.click("New attempt (new run ID)");
    assert.match(page.text(), /lost new-run response/);
    await page.click("Refresh lesson and state");
    page.answer("after recovery");
    await page.click("Submit prediction");
    assert.equal(page.calls.find(call => call.route === "/attempt").body.run_id, "run-2");
  }],
  ["uncertain retry keeps the exact old payload after run changes", async () => {
    const page = await mounted();
    page.onAttempt = () => { page.context.run_id = "run-2"; throw Error("delivery uncertain"); };
    page.answer("  Exact answer\n");
    await page.click("Submit prediction");
    await page.click("Refresh lesson and state");
    assert.match(page.text(), /Run: run-2/);
    await page.click("Retry same submission");
    const submissions = page.calls.filter(call => call.route === "/attempt");
    assert.equal(submissions.length, 2);
    assert.deepEqual(submissions[0].body, { context_id: "ctx-1", run_id: "run-1", answer: "  Exact answer\n" });
    assert.deepEqual(submissions[1].body, submissions[0].body);
  }],
  ["exact committed readback resolves uncertain submission", async () => {
    const page = await mounted();
    page.onAttempt = body => {
      page.state.attempts.push({ id: "committed", ...copy(body), status: "awaiting_assessment", assistance: "none" });
      throw Error("lost submit response");
    };
    page.answer("committed answer");
    await page.click("Submit prediction");
    assert.doesNotMatch(page.text(), /Delivery uncertain/);
    assert.match(page.text(), /Committed attempt: awaiting assessment/);
    assert.match(page.text(), /lost submit response/); // Readback must not hide the failed request.
    assert.equal(page.calls.filter(call => call.route === "/attempt").length, 1);
  }],
  ["different context, run, answer or store cannot resolve pending delivery", async () => {
    for (const mismatch of ["context_id", "run_id", "answer", "store_id"]) {
      const page = await mounted();
      page.onAttempt = body => {
        const attempt = { id: "other", ...copy(body), status: "awaiting_assessment", assistance: "none" };
        if (mismatch === "store_id") page.state.store_id = "store-2";
        else attempt[mismatch] = "different";
        page.state.attempts.push(attempt);
        throw Error("lost response");
      };
      page.answer("original answer");
      await page.click("Submit prediction");
      assert.match(page.text(), /Delivery uncertain/, mismatch);
      if (mismatch === "store_id") {
        assert.match(page.text(), /Read-only/);
        assert.equal(page.button("Retry same submission").props.disabled, true);
      }
    }
  }],
  ["mismatched success response is not accepted as the submitted answer", async () => {
    const page = await mounted();
    page.onAttempt = body => ({ attempt: { id: "wrong", ...copy(body), answer: "other answer" } });
    page.answer("original answer");
    await page.click("Submit prediction");
    assert.match(page.text(), /Invalid attempt response/);
    assert.match(page.text(), /Delivery uncertain/);
  }]
];
(async () => {
  let failed = 0;
  for (const [name, test] of tests) {
    try { await test(); console.log(`PASS ${name}`); }
    catch (error) { failed++; console.error(`FAIL ${name}\n${error.stack}`); }
  }
  console.log(`${tests.length - failed}/${tests.length} recovery checks passed; adapters identical`);
  process.exitCode = failed ? 1 : 0;
})();
