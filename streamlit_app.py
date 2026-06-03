"""Streamlit web UI for Avouch.

A thin, interactive front-end over the Avouch engine. Lets a user pick a
target, judge, objective, and mode, run a red-teaming attack, and see the
scorecard rendered in the browser. Also exposes the judge calibration report.

Run with:  poetry run streamlit run streamlit_app.py
"""

import streamlit as st

from avouch.adapters.registry import available_providers, get_adapter
from avouch.agents.objectives import OBJECTIVE_LIBRARY, get_objective
from avouch.agents.runner import run_attack
from avouch.agents.types import Outcome
from avouch.eval.harness import evaluate_judge
from avouch.orchestrator.run import run_adaptive_attack

st.set_page_config(page_title="Avouch", page_icon="🛡️", layout="centered")

st.title("🛡️ Avouch")
st.caption("An agentic red-teaming and evaluation framework for LLM safety.")

tab_attack, tab_eval = st.tabs(["Run Attack", "Judge Calibration"])


with tab_attack:
    st.subheader("Configure a red-teaming run")

    providers = available_providers()
    objectives = sorted(OBJECTIVE_LIBRARY)

    col1, col2 = st.columns(2)
    with col1:
        target_name = st.selectbox(
            "Target (model under test)",
            providers,
            index=providers.index("cerebras") if "cerebras" in providers else 0,
        )
    with col2:
        judge_name = st.selectbox(
            "Judge (different family advised)",
            providers,
            index=providers.index("groq") if "groq" in providers else 0,
        )

    objective_name = st.selectbox("Objective", objectives)
    adaptive = st.toggle("Adaptive mode (LangGraph orchestrator with critic loop)")
    max_attempts = st.slider("Max attempts", min_value=1, max_value=4, value=4)

    if st.button("Run Attack", type="primary"):
        objective = get_objective(objective_name)
        target = get_adapter(target_name)
        judge = get_adapter(judge_name)

        with st.spinner("Running attack (several model calls)..."):
            if adaptive:
                result = run_adaptive_attack(
                    target, judge, objective, max_attempts=max_attempts
                )
            else:
                result = run_attack(target, judge, objective, max_attempts=max_attempts)

        if result.succeeded:
            st.error("RESULT: The target BROKE its rule on at least one attempt.")
        else:
            st.success("RESULT: The target HELD its rule on all attempts.")

        st.subheader("Scorecard")
        for verdict in result.verdicts:
            attempt = verdict.attempt
            broke = verdict.outcome is Outcome.SUCCESS
            label = "BROKEN" if broke else verdict.outcome.value.upper()
            with st.expander(
                f"Attempt {attempt.attempt_number} — {attempt.technique.value} → {label}",
                expanded=False,
            ):
                st.markdown(f"**Judge reasoning:** {verdict.reasoning}")
                st.markdown("**Attack prompt:**")
                st.code(attempt.attack_prompt)
                st.markdown("**Target response:**")
                st.code(attempt.target_response)


with tab_eval:
    st.subheader("Validate the judge against golden test cases")
    st.write(
        "Runs the judge against hand-labeled cases to measure calibration. "
        "Missed breaches (the judge failing to catch a real rule break) are "
        "the dangerous error type."
    )

    eval_judge_name = st.selectbox(
        "Judge to evaluate",
        available_providers(),
        index=available_providers().index("groq")
        if "groq" in available_providers()
        else 0,
        key="eval_judge",
    )

    if st.button("Run Calibration", type="primary"):
        judge = get_adapter(eval_judge_name)
        with st.spinner("Running golden test cases..."):
            report = evaluate_judge(judge)

        c1, c2, c3 = st.columns(3)
        c1.metric("Accuracy", f"{report.accuracy * 100:.0f}%")
        c2.metric("Missed breaches", report.missed_breaches)
        c3.metric("False alarms", report.false_alarms)

        st.subheader("Per-case results")
        for r in report.results:
            icon = "✅" if r.agreed else "❌"
            st.write(
                f"{icon} **{r.case_id}** — expected `{r.expected.value}`, "
                f"got `{r.actual.value}`"
            )
