import streamlit as st
import LED
import Nash

st.title("Meine App")

if st.button("Starte LED"):
    with st.spinner("LED-Skript laeuft auf dem Pico..."):
        try:
            result = LED.run(port="COM3")
        except Exception as exc:
            st.error(f"LED konnte nicht gestartet werden: {exc}")
        else:
            st.success("LED-Skript wurde ausgefuehrt.")
            st.write("Erkannte Ports:")
            st.code(result["ports"])
            if result["stdout"]:
                st.write("Ausgabe:")
                st.code(result["stdout"])
            if result["stderr"] or result["ports_error"]:
                st.warning("Fehlerausgabe:")
                st.code("\n".join(filter(None, [result["ports_error"], result["stderr"]])))

if st.button("Starte Nash"):
    Nash.run()
