# DynamicWriter

A local web app for analyzing your own writing, drafting a new paper in your voice, and revising it with your feedback. You can edit the extracted samples, writing profile, rubric, and paper at any time.

## Run locally

Requires Python 3.9 or newer and an OpenAI API key with access to the chosen model.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
python app.py
```

Open http://127.0.0.1:8000. Set `PORT` to change the port, or `OPENAI_MODEL` to choose another OpenAI chat-completions model (default: `gpt-4o-mini`). API usage may incur charges.

1. Upload up to 10 of your own writing samples, review their extracted text, and select **Analyze my writing**. Edit the resulting profile if needed.
2. Describe the assignment, optionally upload or paste a rubric, and add any comments or guidance. Select **Write a draft**.
3. Edit the draft directly, then provide revision instructions and select **Revise my paper** as often as needed. Download the finished paper as a text file.

Uploads accept UTF-8 `.txt` and `.md`, `.docx`, and text-based `.pdf` files, up to 5 MB each and 120,000 extracted characters each. PDFs are limited to 100 pages; scanned PDFs need OCR first. Tables and complex formatting may not be preserved, so review extracted text.

Files are extracted on your computer. When you select an AI action, the app sends your writing samples and the relevant profile, assignment, rubric, guidance, or draft to OpenAI for processing under its applicable data policies. The app does not save your work; refreshing or closing the page loses it. Download your paper before leaving. The API key remains on the server and is not sent to the browser. Review generated content, verify claims and sources, and follow applicable academic integrity rules.

## Tests

```sh
python -m unittest -v
```