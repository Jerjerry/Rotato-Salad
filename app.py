import streamlit as st
from datetime import datetime
import io

# --- Core Logic Class ---
class ProductionRotation:
    """Handles the logic for generating station rotation pairs."""
    def __init__(self):
        self.lines = ['B', 'C', 'L', 'M', 'N', 'O']
        self.stations = list(range(1, 21))
        self.non_operational_stations = {}
        self.fixed_stations = {}

    def set_non_operational(self, line, stations):
        self.non_operational_stations[line] = sorted(list(set(stations)))

    def set_fixed(self, line, stations):
        self.fixed_stations[line] = sorted(list(set(stations)))

    def get_operational_stations(self, line):
        temp_non_operational = self.non_operational_stations.get(line, [])
        return sorted([s for s in self.stations if s not in temp_non_operational])

    def generate_pairs(self, line):
        operational = self.get_operational_stations(line)
        if not operational:
            return []
        if line == 'C':
            fixed = self.fixed_stations.get(line, [])
            valid_fixed = [s for s in fixed if s in operational]
            fixed_pairs = [f"{s}-{s}" for s in valid_fixed]
            remaining = [s for s in operational if s not in valid_fixed]
            return fixed_pairs + self.mirror_pair(remaining)
        return self.mirror_pair(operational)

    def mirror_pair(self, stations):
        sorted_stations = sorted(stations)
        pairs = []
        n = len(sorted_stations)
        for i in range(n // 2):
            pairs.append(f"{sorted_stations[i]}-{sorted_stations[n - 1 - i]}")
        if n % 2 != 0:
            middle_index = n // 2
            pairs.append(f"{sorted_stations[middle_index]}-{sorted_stations[middle_index]}")
        return pairs

    def generate_schedule(self):
        date = datetime.now().strftime("%m/%d/%Y")
        schedule = {}
        for line in self.lines:
            pairs = self.generate_pairs(line)
            schedule[line] = pairs
        return date, schedule

# --- Session State Management ---
def initialize_session_state():
    lines = ['B', 'C', 'L', 'M', 'N', 'O']
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    if 'last_date' not in st.session_state or st.session_state.last_date != current_date_str:
        st.session_state.last_date = current_date_str
        st.session_state.non_operational = {line: [] for line in lines}
        st.session_state.accommodation_c = []
        st.session_state.has_accommodation_c = False
        for line in lines:
            st.session_state.pop(f"non_op_{line}", None)
        st.session_state.pop("accommodation_stations_c", None)
    for key, default in [('non_operational', {L:[] for L in lines}), ('accommodation_c', []), ('has_accommodation_c', False)]:
        if key not in st.session_state: st.session_state[key] = default

def update_session_state_on_submit():
    lines = ['B', 'C', 'L', 'M', 'N', 'O']
    for line in lines:
        st.session_state.non_operational[line] = st.session_state.get(f"non_op_{line}", [])
    st.session_state.has_accommodation_c = len(st.session_state.get("accommodation_stations_c", [])) > 0
    st.session_state.accommodation_c = st.session_state.get("accommodation_stations_c", [])

# --- HTML Generation ---
def generate_print_friendly_html(date, schedule):
    html = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Station Rotation - {date}</title>
        <style>
            @media print {{ @page {{ size: A4; margin: 10mm; }} body {{ margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }} .no-print {{ display: none !important; }} }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: white; color: #1c1c1e; font-size: 10pt; margin: 10mm; line-height: 1.2; position: relative; }}
            .container {{ max-width: 100%; box-sizing: border-box; }}
            .header {{ text-align: center; margin-bottom: 8mm; padding-bottom: 4mm; border-bottom: 1px solid #d1d1d6; }}
            .title {{ font-size: 16pt; font-weight: bold; margin: 0; text-transform: uppercase; color: #1c1c1e; }}
            .date {{ font-size: 10pt; margin: 3mm 0; color: #8e8e93; }}
            .columns {{ display: flex; justify-content: space-between; gap: 8mm; }}
            .column {{ flex: 1; max-width: 48%; }}
            .line-group {{ margin-bottom: 6mm; page-break-inside: avoid; }}
            .line-title {{ font-size: 12pt; font-weight: 600; text-align: center; margin-bottom: 3mm; padding: 2mm 4mm; background-color: #f2f2f7; text-transform: uppercase; color: #1c1c1e; border-radius: 4px; }}
            .pairs {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 3mm; padding: 0 2mm; }}
            .pair {{ padding: 3mm 4mm; border: 1px solid #d1d1d6; border-radius: 4px; font-size: 10pt; text-align: center; background-color: white; color: #1c1c1e; }}
            .empty-message {{ font-style: italic; color: #8e8e93; text-align: center; padding: 3mm; font-size: 10pt; grid-column: 1 / -1; }}
            .watermark {{ margin-top: 40px; text-align: center; opacity: 0.15; font-size: 12pt; }}
        </style>
    </head>
    <body>
        <div class='container'>
            <div class='header'> <div class='title'>Station Rotation</div> <div class='date'>Date: {date}</div> </div>
            <div class='columns'>
                <div class='column'>
    """
    for line in ['B', 'C', 'L']:
        html += f'<div class="line-group"><div class="line-title">Line {line}</div><div class="pairs">'
        if not schedule.get(line):
            html += '<div class="empty-message">No pairs generated</div>'
        else:
            for pair in schedule[line]:
                html += f'<div class="pair">{pair}</div>'
        html += '</div></div>'
    html += '</div><div class="column">'
    for line in ['M', 'N', 'O']:
        html += f'<div class="line-group"><div class="line-title">Line {line}</div><div class="pairs">'
        if not schedule.get(line):
            html += '<div class="empty-message">No pairs generated</div>'
        else:
            for pair in schedule[line]:
                html += f'<div class="pair">{pair}</div>'
        html += '</div></div>'
    html += f"""
            </div>
        </div>
        <div class='watermark'>
            <img src='https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg' alt='Amazon Logo' style='height: 30px; vertical-align: middle;'>
            <div style='margin-top: 4px;'>jerjerry</div>
        </div>
    </div></body></html>"""
    return html

# --- Main Application ---
def main():
    st.set_page_config(page_title="Station Rotation", layout="wide")
    st.title("Station Rotation")

    initialize_session_state()
    rotation = ProductionRotation()
    all_stations_list = rotation.stations
    lines_list = rotation.lines

    with st.form(key="station_config_form", clear_on_submit=False):
        st.header("Station Configuration")
        st.subheader("Temporarily Unavailable Stations")
        st.caption("Select stations temporarily unavailable for today on each line.")

        for line in lines_list:
            available_stations_for_line = all_stations_list

            if line == 'C':
                accommodation_options_c = available_stations_for_line
                accommodated_stations_c = st.multiselect(
                    "Line C Accommodations",
                    options=accommodation_options_c,
                    default=st.session_state.get("accommodation_c", []),
                    key="accommodation_stations_c",
                    help="Select the specific station(s) that require accommodation on Line C today."
                )

                available_for_down_c = [s for s in available_stations_for_line if s not in accommodated_stations_c]

                if available_for_down_c:
                    st.multiselect(
                        "Line C",
                        options=available_for_down_c,
                        default=st.session_state.non_operational.get(line, []),
                        key=f"non_op_{line}",
                        help=f"Select stations temporarily unavailable today on Line C (excluding accommodations)."
                    )
                else:
                    st.info("No additional stations available to be marked as down on Line C after selecting accommodations.")

            else:
                if not available_stations_for_line:
                    st.warning(f"No stations available for Line {line}.")
                else:
                    st.multiselect(
                        f"Line {line}",
                        options=available_stations_for_line,
                        default=st.session_state.non_operational.get(line, []),
                        key=f"non_op_{line}",
                        help=f"Select stations temporarily unavailable today on Line {line}."
                    )

        st.divider()
        submitted = st.form_submit_button(
            "Generate & Download",
            on_click=update_session_state_on_submit,
            type="primary",
            use_container_width=True
        )

    if submitted:
        st.header("Download")
        for line in lines_list:
            rotation.set_non_operational(line, st.session_state.non_operational.get(line, []))
        rotation.set_fixed('C', st.session_state.get("accommodation_c", []))

        current_date_display, schedule_data = rotation.generate_schedule()

        if all(not pairs for pairs in schedule_data.values()):
            st.error("No operational stations available across any lines based on current settings. Cannot generate a schedule.")
        else:
            html_content = generate_print_friendly_html(current_date_display, schedule_data)
            html_buffer = io.BytesIO(html_content.encode('utf-8'))
            st.download_button(
                label="Click Here to Download HTML",
                data=html_buffer,
                file_name=f"station_rotation_{current_date_display.replace('/', '-')}.html",
                mime="text/html",
                use_container_width=True,
                key='download_button'
            )
            st.success("HTML file ready. Click the button above to download.")

    elif 'last_date' not in st.session_state:
        st.info("Configure station settings using the form above and click 'Generate & Download'.")

if __name__ == "__main__":
    main()
