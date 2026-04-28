import streamlit as st
import time


def run():
    loading_text = st.empty()

    latest_iteration = st.empty()
    bar = st.progress(0)
    dots = "."
    last_dot_update = time.time()
    loading_text.text(f"Soul is a snuifduif loading{dots}")

    for i in range(100):
        if time.time() - last_dot_update >= 1:
            dots = "." if dots == "....." else dots + "."
            loading_text.text(f"Soul is a snuifduif loading{dots}")
            last_dot_update = time.time()

        latest_iteration.text(f"{i + 1}%")
        bar.progress(i + 1)
        time.sleep(0.1)

    loading_text.text("Soul is a snuifduif loading...")
    st.success("Soul has been snuifduifed.")


if __name__ == "__main__":
    run()