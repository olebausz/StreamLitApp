import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import LED
import Nash
import Soul
import Temp_ext

st.title("Meine App")

components.html(
    """
    <script>
    const storageKey = "streamlit-temperature-scroll-y";
    const greenLabels = new Set(["Messung starten", "LED ein"]);
    const redLabels = new Set(["Messung stoppen", "LED aus"]);

    const applyButtonStyle = (button, color) => {
        if (button.disabled) {
            button.style.backgroundColor = "";
            button.style.borderColor = "";
            button.style.color = "";
            return;
        }

        button.style.backgroundColor = color;
        button.style.borderColor = color;
        button.style.color = "white";
    };

    const styleActionButtons = () => {
        window.parent.document.querySelectorAll("button").forEach((button) => {
            const label = button.innerText.trim();
            if (greenLabels.has(label)) {
                applyButtonStyle(button, "#16a34a");
            } else if (redLabels.has(label)) {
                applyButtonStyle(button, "#dc2626");
            }
        });
    };

    const restore = () => {
        const y = window.parent.sessionStorage.getItem(storageKey);
        if (y !== null) {
            window.parent.scrollTo(0, Number(y));
        }
    };
    restore();
    window.parent.setTimeout(restore, 50);
    window.parent.addEventListener("scroll", () => {
        window.parent.sessionStorage.setItem(storageKey, window.parent.scrollY);
    }, { passive: true });
    styleActionButtons();
    window.parent.setTimeout(styleActionButtons, 50);
    window.parent.setTimeout(styleActionButtons, 250);
    new MutationObserver(styleActionButtons).observe(window.parent.document.body, {
        childList: true,
        subtree: true,
    });
    </script>
    """,
    height=0,
)

if "temperature_measurement" not in st.session_state:
    st.session_state.temperature_measurement = Temp_ext.create_measurement(port="COM3")

if "led_enabled" not in st.session_state:
    st.session_state.led_enabled = False

if "led_message" not in st.session_state:
    st.session_state.led_message = "LED ist ausgeschaltet."

if "led_message_type" not in st.session_state:
    st.session_state.led_message_type = "info"

if "port_check_result" not in st.session_state:
    st.session_state.port_check_result = None

if "nash_output_visible" not in st.session_state:
    st.session_state.nash_output_visible = False

if "soul_output_visible" not in st.session_state:
    st.session_state.soul_output_visible = False

st.header("Temperaturmessung")

measurement = st.session_state.temperature_measurement
refresh_interval = "1s" if measurement.is_running() else None


@st.fragment(run_every=refresh_interval)
def temperature_section():
    measurement = st.session_state.temperature_measurement
    measurement.drain()

    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("Messung starten", disabled=measurement.is_running()):
            try:
                measurement.start()
            except Exception as exc:
                st.error(f"Messung konnte nicht gestartet werden: {exc}")
            else:
                st.rerun(scope="app")

    with col_stop:
        if st.button("Messung stoppen", disabled=not measurement.is_running()):
            measurement.stop()
            st.rerun(scope="app")

    return_code = measurement.return_code()
    if measurement.is_running():
        status = "laeuft"
    elif return_code is None:
        status = "gestoppt"
    else:
        status = f"beendet (Exit-Code {return_code})"
    st.write(f"Status: {status}")

    value_placeholder = st.empty()
    chart_placeholder = st.empty()

    if measurement.values:
        current_temp = measurement.values[-1]
        if measurement.internal_values:
            current_internal_temp = measurement.internal_values[-1]
            if current_internal_temp < current_temp:
                internal_indicator = "↓"
            elif current_internal_temp > current_temp:
                internal_indicator = "↑"
            else:
                internal_indicator = "→"

            value_placeholder.metric(
                "Aktuelle Temperatur",
                f"{current_temp:.2f} C",
                f"{internal_indicator} {current_internal_temp:.2f} C intern",
                delta_color="off",
            )
        else:
            value_placeholder.metric("Aktuelle Temperatur", f"{current_temp:.2f} C")

        chart_col_external, chart_col_internal = st.columns(2)
        external_x = range(1, len(measurement.values) + 1)
        fig_external, ax_external = plt.subplots(figsize=(5.8, 3.2))
        ax_external.plot(
            external_x,
            measurement.values,
            color="orange",
            label="Externer Sensor",
        )
        ax_external.set_title("Externer Sensor")
        ax_external.set_xlabel("Messung")
        ax_external.set_ylabel("Temperatur (C)")
        ax_external.grid(True, alpha=0.3)
        ax_external.legend()
        chart_col_external.pyplot(fig_external, clear_figure=True)
        plt.close(fig_external)

        if measurement.internal_values:
            internal_x = range(1, len(measurement.internal_values) + 1)
            fig_internal, ax_internal = plt.subplots(figsize=(5.8, 3.2))
            ax_internal.plot(
                internal_x,
                measurement.internal_values,
                label="Pico intern",
            )
            ax_internal.set_title("Pico intern")
            ax_internal.set_xlabel("Messung")
            ax_internal.set_ylabel("Temperatur (C)")
            ax_internal.grid(True, alpha=0.3)
            ax_internal.legend()
            chart_col_internal.pyplot(fig_internal, clear_figure=True)
            plt.close(fig_internal)
        else:
            chart_col_internal.info("Noch keine internen Temperaturwerte empfangen.")
    else:
        value_placeholder.info("Noch keine Temperaturwerte empfangen.")
        chart_placeholder.empty()

    if measurement.ignored_external_values:
        with st.expander(
            f"Verworfene Werte: {measurement.ignored_external_values}",
            expanded=False,
        ):
            ignored_lines = []
            for measurement_number, external_temp, internal_temp in measurement.ignored_value_pairs:
                if internal_temp is None:
                    ignored_lines.append(
                        f"Messung {measurement_number}: Extern: {external_temp:.2f} C"
                    )
                else:
                    ignored_lines.append(
                        f"Messung {measurement_number}: Extern: {external_temp:.2f} C, "
                        f"Intern: {internal_temp:.2f} C"
                    )

            st.code("\n".join(ignored_lines))

    if st.button(
        "Clear Output",
        disabled=(
            not measurement.values
            and not measurement.internal_values
            and not measurement.raw_messages
            and not measurement.ignored_external_values
        ),
    ):
        measurement.clear_output()
        st.rerun(scope="app")

    if measurement.raw_messages:
        with st.expander("Pico-Ausgabe"):
            st.code("\n".join(measurement.raw_messages[-20:]))


temperature_section()

st.divider()

st.header("LED")

if st.session_state.led_message:
    if st.session_state.led_message_type == "success":
        st.success(st.session_state.led_message)
    else:
        st.info(st.session_state.led_message)

led_on_col, led_off_col = st.columns(2)
with led_on_col:
    if st.button("LED ein", disabled=st.session_state.led_enabled):
        with st.spinner("LED wird eingeschaltet..."):
            try:
                result = LED.set_led(True, port="COM3")
            except Exception as exc:
                st.error(f"LED konnte nicht eingeschaltet werden: {exc}")
            else:
                if result["stderr"]:
                    st.error(result["stderr"])
                else:
                    st.session_state.led_enabled = True
                    st.session_state.led_message = "LED ist eingeschaltet."
                    st.session_state.led_message_type = "success"
                    st.rerun()

with led_off_col:
    if st.button("LED aus", disabled=not st.session_state.led_enabled):
        with st.spinner("LED wird ausgeschaltet..."):
            try:
                result = LED.set_led(False, port="COM3")
            except Exception as exc:
                st.error(f"LED konnte nicht ausgeschaltet werden: {exc}")
            else:
                if result["stderr"]:
                    st.error(result["stderr"])
                else:
                    st.session_state.led_enabled = False
                    st.session_state.led_message = "LED ist ausgeschaltet."
                    st.session_state.led_message_type = "info"
                    st.rerun()

st.divider()
st.header("Port Check")

if st.button("Port Check"):
    try:
        result = LED.port_check()
    except Exception as exc:
        st.error(f"Port Check fehlgeschlagen: {exc}")
    else:
        st.session_state.port_check_result = result

if st.session_state.port_check_result:
    result = st.session_state.port_check_result
    st.write("Erkannte Ports:")
    st.code(result["ports"])
    st.info(result["hint"])
    if result["stderr"]:
        st.warning("Fehlerausgabe:")
        st.code(result["stderr"])

if st.button("Clear Output", disabled=not st.session_state.port_check_result, key="clear_port_check"):
    st.session_state.port_check_result = None
    st.rerun()

st.divider()

st.header("Shenanigans")

if st.button("Starte Nash"):
    st.session_state.nash_output_visible = True
    with st.container():
        Nash.run()

if st.session_state.nash_output_visible:
    if st.button("Clear Output", key="clear_nash_output"):
        st.session_state.nash_output_visible = False
        st.rerun()

if st.button("Starte Soul"):
    st.session_state.soul_output_visible = True
    with st.container():
        Soul.run()

if st.session_state.soul_output_visible:
    if st.button("Clear Output", key="clear_soul_output"):
        st.session_state.soul_output_visible = False
        st.rerun()
