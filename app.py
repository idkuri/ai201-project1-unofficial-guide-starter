import gradio as gr

from generator import _content_to_text, ask, format_context_log_entry
from ingest import chunk_document, load_documents
from retriever import embed_and_store, get_collection


def run_ingestion():
    """
    Load documents, chunk them, and store in ChromaDB.

    If the vector store is already populated, ingestion is skipped.
    To re-ingest (e.g. after changing your chunking strategy), delete the
    ./chroma_db folder and restart the app.
    """
    collection = get_collection()

    if collection.count() > 0:
        print(f"Vector store already populated ({collection.count()} chunks). Skipping ingestion.")
        print("To re-ingest, delete the ./chroma_db folder and restart.")
        return

    print("Ingesting documents...")
    documents = load_documents()
    all_chunks = []

    for doc in documents:
        chunks = chunk_document(doc["text"], doc["source"])
        all_chunks.extend(chunks)

    if all_chunks:
        embed_and_store(all_chunks)
        print(f"Ingestion complete. {len(all_chunks)} chunks stored.")
    else:
        print(
            "\nNo chunks produced. Make sure chunk_document() is implemented in ingest.py\n"
            "and that you have .txt files in the documents/ folder.\n"
            "The app will start, but won't be able to answer questions yet.\n"
        )


def handle_query(question, retrieval_mode):
    """Run retrieval + generation; return answer and review citations separately."""
    if not question.strip():
        return "", ""
    result = ask(question, retrieval_mode=retrieval_mode)
    citations = "\n\n".join(result["citations"]) if result.get("citations") else ""
    return result["answer"], citations


def _as_chat_messages(history) -> list[dict]:
    """Normalize Gradio 6 messages or legacy [user, bot] pairs for the Chatbot."""
    if not history:
        return []

    messages = []
    for turn in history:
        if isinstance(turn, dict) and "role" in turn and "content" in turn:
            content = _content_to_text(turn["content"])
            messages.append({"role": turn["role"], "content": content})
        elif isinstance(turn, (list, tuple)):
            if len(turn) > 0:
                user_msg = _content_to_text(turn[0])
                if user_msg:
                    messages.append({"role": "user", "content": user_msg})
            if len(turn) > 1:
                assistant_msg = _content_to_text(turn[1])
                if assistant_msg:
                    messages.append({"role": "assistant", "content": assistant_msg})
    return messages


def _turn_label(turn_num: int) -> str:
    return f"Turn {turn_num}"


def _turn_index(label: str | None) -> int | None:
    if not label:
        return None
    try:
        return int(label.rsplit(" ", 1)[-1]) - 1
    except ValueError:
        return None


def chat_submit(message, history, retrieval_mode, citations_by_turn, context_log):
    """Answer in the chatbot; store citations and context separately."""
    history = _as_chat_messages(history)

    if not message.strip():
        return (
            history,
            "",
            citations_by_turn,
            context_log,
            "",
            gr.update(),
            gr.update(open=False),
            context_log or "*(no messages yet)*",
        )

    result = ask(message, retrieval_mode=retrieval_mode, history=history)
    answer = result["answer"]
    citations = result.get("citations") or []
    citations_text = "\n\n".join(citations) if citations else "No reviews were retrieved for this response."

    turn_num = len(citations_by_turn) + 1
    entry = format_context_log_entry(turn_num, message, history)
    new_context_log = f"{context_log}\n\n---\n\n{entry}" if context_log else entry

    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    new_citations = list(citations_by_turn or []) + [citations_text]
    turn_label = _turn_label(turn_num)

    return (
        new_history,
        "",
        new_citations,
        new_context_log,
        citations_text,
        gr.update(choices=[_turn_label(i) for i in range(1, turn_num + 1)], value=turn_label),
        gr.update(open=bool(citations)),
        new_context_log,
    )


def show_sources(turn_label, citations_by_turn):
    """Expand the sources panel for the selected turn."""
    idx = _turn_index(turn_label)
    if idx is None or not citations_by_turn or idx >= len(citations_by_turn):
        return "", gr.update(open=False)
    return citations_by_turn[idx], gr.update(open=True)


def clear_chat():
    return (
        [],
        "",
        [],
        "",
        "",
        gr.update(choices=[], value=None),
        gr.update(open=False),
        "*(no messages yet)*",
    )


with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue"),
    title="The Unofficial Guide",
) as demo:

    gr.HTML("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="margin: 0;">The Unofficial Guide</h1>
        <p style="color: #666; margin-top: 0.5rem;">
            Ask about Stony Brook CS professors — answers grounded in Rate My Professors reviews.
        </p>
    </div>
    """)

    retrieval_mode = gr.Radio(
        choices=["semantic", "hybrid"],
        value="semantic",
        label="Retrieval mode",
        info="Hybrid combines semantic search + BM25 keywords (extra credit).",
    )

    with gr.Tabs():
        with gr.Tab("Ask"):
            with gr.Row():
                with gr.Column(scale=3):
                    question_box = gr.Textbox(
                        label="Your question",
                        placeholder='e.g. "Does Paul Fodor record his lectures for CSE 114?"',
                        lines=2,
                    )
                    ask_btn = gr.Button("Ask", variant="primary")

                    with gr.Row():
                        answer_box = gr.Textbox(label="Answer", lines=10, interactive=False)
                        sources_box = gr.Textbox(label="Retrieved from", lines=24, interactive=False)

                    ask_btn.click(
                        handle_query,
                        inputs=[question_box, retrieval_mode],
                        outputs=[answer_box, sources_box],
                    )
                    question_box.submit(
                        handle_query,
                        inputs=[question_box, retrieval_mode],
                        outputs=[answer_box, sources_box],
                    )

                    gr.Examples(
                        examples=[
                            "Does Paul Fodor record his lectures for CSE 114?",
                            "What Rate My Professor tags do students assign to Christopher Kane for CSE 307?",
                            "What do students say about I.V. Ramakrishnan's CSE 596 class?",
                            "What's the best dining hall at Stony Brook?",
                        ],
                        inputs=question_box,
                    )

                with gr.Column(scale=1, min_width=180):
                    gr.HTML("""
                    <div style="padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                        <h3 style="margin-top: 0;">How it works</h3>
                        <p style="font-size: 0.9rem; color: #555;">
                            Type a question and click <strong>Ask</strong>.
                            The system retrieves relevant student reviews, then generates
                            an answer using only those reviews.
                        </p>
                        <p style="font-size: 0.85rem; color: #777;">
                            Sources are listed separately on the right — not generated by the LLM.
                            If the info isn't in the loaded reviews, the guide will say so.
                        </p>
                    </div>
                    """)

        with gr.Tab("Chat"):
            gr.Markdown(
                "Ask follow-up questions like *\"Does he record lectures?\"* after discussing a "
                "professor. Answers appear in the chat; use **Show sources** below any response "
                "to expand retrieved reviews. The **AI context log** on the right shows how prior "
                "turns and query expansion feed into each answer."
            )

            citations_by_turn = gr.State([])
            context_log_state = gr.State("")

            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(label="Chat", height=420)
                    chat_input = gr.Textbox(
                        label="Message",
                        placeholder='e.g. "What do students say about Paul Fodor?" then "Does he record lectures?"',
                        lines=2,
                    )
                    with gr.Row():
                        chat_send = gr.Button("Send", variant="primary")
                        chat_clear = gr.Button("Clear chat")
                    with gr.Row():
                        turn_select = gr.Dropdown(
                            label="Sources for turn",
                            choices=[],
                            value=None,
                            scale=2,
                        )
                        show_sources_btn = gr.Button("Show sources", scale=1)

                    with gr.Accordion("Retrieved reviews", open=False) as sources_accordion:
                        chat_sources = gr.Textbox(
                            label="",
                            lines=14,
                            interactive=False,
                            show_label=False,
                        )

                with gr.Column(scale=2):
                    gr.Markdown("#### AI context log")
                    context_log_display = gr.Markdown(value="*(no messages yet)*")

            chat_inputs = [chat_input, chatbot, retrieval_mode, citations_by_turn, context_log_state]
            chat_outputs = [
                chatbot,
                chat_input,
                citations_by_turn,
                context_log_state,
                chat_sources,
                turn_select,
                sources_accordion,
                context_log_display,
            ]

            chat_send.click(chat_submit, chat_inputs, chat_outputs)
            chat_input.submit(chat_submit, chat_inputs, chat_outputs)
            show_sources_btn.click(
                show_sources,
                inputs=[turn_select, citations_by_turn],
                outputs=[chat_sources, sources_accordion],
            )
            turn_select.change(
                show_sources,
                inputs=[turn_select, citations_by_turn],
                outputs=[chat_sources, sources_accordion],
            )
            chat_clear.click(
                clear_chat,
                outputs=[
                    chatbot,
                    chat_input,
                    citations_by_turn,
                    context_log_state,
                    chat_sources,
                    turn_select,
                    sources_accordion,
                    context_log_display,
                ],
            )

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  The Unofficial Guide — starting up")
    print("=" * 50 + "\n")
    run_ingestion()
    demo.launch()
