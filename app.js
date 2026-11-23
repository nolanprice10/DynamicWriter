"use strict";

const $ = id => document.getElementById(id);
let busy = false;

function status(message, error = false) {
  $("status").textContent = message;
  $("status").classList.toggle("error", error);
}

async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data.text;
}

async function extract(file) {
  if (file.size > 5 * 1024 * 1024) throw new Error(`${file.name}: file must be 5 MB or smaller.`);
  const encoded = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]);
    reader.onerror = () => reject(new Error(`Could not read ${file.name}.`));
    reader.readAsDataURL(file);
  });
  return post("/api/extract", {name: file.name, content: encoded});
}

function addSample(name, text) {
  const container = document.createElement("div");
  container.className = "sample";
  const label = document.createElement("label");
  const textarea = document.createElement("textarea");
  textarea.rows = 6;
  textarea.value = text;
  textarea.id = `sample-${crypto.randomUUID()}`;
  label.htmlFor = textarea.id;
  label.textContent = name;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "secondary";
  remove.textContent = "Remove sample";
  remove.addEventListener("click", () => container.remove());
  container.append(label, textarea, remove);
  $("sample-list").append(container);
}

async function run(operation, label) {
  if (busy) return;
  busy = true;
  document.querySelectorAll("button, input[type=file], textarea").forEach(element => element.disabled = true);
  status(label);
  try {
    await operation();
    status("Done.");
  } catch (error) {
    status(error.message || "Something went wrong.", true);
  } finally {
    busy = false;
    document.querySelectorAll("button, input[type=file], textarea").forEach(element => element.disabled = false);
  }
}

$("samples").addEventListener("change", event => {
  const files = Array.from(event.target.files);
  event.target.value = "";
  run(async () => {
    if (files.length + document.querySelectorAll(".sample").length > 10) throw new Error("You can upload up to 10 writing samples.");
    for (const file of files) addSample(file.name, await extract(file));
  }, "Extracting writing samples…");
});

$("rubric-file").addEventListener("change", event => {
  const file = event.target.files[0];
  event.target.value = "";
  if (file) run(async () => { $("rubric").value = await extract(file); }, "Extracting rubric…");
});

function payload(action) {
  return {
    action,
    samples: Array.from(document.querySelectorAll(".sample textarea"), element => element.value),
    profile: $("profile").value,
    assignment: $("assignment").value,
    rubric: $("rubric").value,
    guidance: $("guidance").value,
    draft: $("draft").value,
    revision: $("revision").value
  };
}

$("analyze").addEventListener("click", () => run(async () => {
  if ($("profile").value.trim() && !confirm("Replace the current writing profile with a new analysis?")) return;
  $("profile").value = await post("/api/generate", payload("analyze"));
}, "Analyzing your writing… This may take a moment."));

$("draft-button").addEventListener("click", () => run(async () => {
  if ($("draft").value.trim() && !confirm("Replace the current paper with a new draft?")) return;
  $("draft").value = await post("/api/generate", payload("draft"));
}, "Writing your draft… This may take a moment."));

$("revise").addEventListener("click", () => run(async () => {
  $("draft").value = await post("/api/generate", payload("revise"));
}, "Revising your paper… This may take a moment."));

$("download").addEventListener("click", () => {
  if (!$("draft").value.trim()) return status("There is no paper to download yet.", true);
  const url = URL.createObjectURL(new Blob([$("draft").value], {type: "text/plain;charset=utf-8"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = "paper.txt";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
