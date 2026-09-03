"""
Milestone 5 — Query interface.

A Gradio front end over the pipeline: a question goes in, a grounded answer
comes out with the student reviews it was built from listed underneath.

    python app.py     # then open http://localhost:7860

Everything below the answer box comes from retrieval metadata, not from the
model, so what you see cited is literally what was fed to the model.
"""

from __future__ import annotations

import gradio as gr

from embed import DEFAULT_K
from generate import ask

EXAMPLES = [
    "What do students say about the difficulty of Jiang Li's exams?",
    "What is the workload like for CSCI 201 with Jiang Li?",
    "What do students say about Gloria Washington's teaching style in CSCI 135?",
    "How do Jiang Li and Jeremy Blackstone compare on workload and exam difficulty?",
    "Is Jeremy Blackstone good for a first programming class?",
]


def handle_query(question: str, k: int):
    question = (question or "").strip()
    if not question:
        return "Type a question about a Howard CS professor or course.", "", ""

    result = ask(question, int(k))

    sources = "\n".join(f"[S{i}] {s}" for i, s in enumerate(result["sources"], 1)) or "(no reviews matched)"

    reviews = "\n\n".join(
        f"[S{i}] distance {chunk['distance']:.3f}\n{chunk['text']}"
        for i, chunk in enumerate(result["chunks"], 1)
    ) or "(nothing retrieved above the relevance cutoff)"

    return result["answer"], sources, reviews


with gr.Blocks(title="Howard CS — The Unofficial Guide") as demo:
    gr.Markdown(
        "# Howard CS — The Unofficial Guide\n"
        "Ask about a Howard University Computer Science professor or course. "
        "Answers come only from 129 student reviews collected from RateMyProfessors — "
        "if the reviews don't cover it, the system says so instead of guessing."
    )

    with gr.Row():
        question = gr.Textbox(
            label="Your question",
            placeholder="e.g. What do students say about Jiang Li's exams?",
            scale=4,
            autofocus=True,
        )
        k = gr.Slider(3, 10, value=DEFAULT_K, step=1, label="Reviews to retrieve (top-k)", scale=1)

    ask_button = gr.Button("Ask", variant="primary")

    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from (professor — course — file — source URL)", lines=6)

    with gr.Accordion("The full reviews behind this answer", open=False):
        reviews = gr.Textbox(label="Retrieved review text", lines=20)

    gr.Examples(examples=EXAMPLES, inputs=question, label="Try one")

    inputs, outputs = [question, k], [answer, sources, reviews]
    ask_button.click(handle_query, inputs=inputs, outputs=outputs)
    question.submit(handle_query, inputs=inputs, outputs=outputs)


if __name__ == "__main__":
    demo.launch()
