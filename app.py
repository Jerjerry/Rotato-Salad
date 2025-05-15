import streamlit as st
from datetime import datetime
import io
from typing import List, Dict, Tuple, Any, Set, Optional

# --- Configuration Constants ---
LINES: List[str] = ['B', 'C', 'L', 'M', 'N', 'O']
STATIONS: List[int] = list(range(1, 21))

# For HTML output columns
LINES_FIRST_COLUMN_HTML: List[str] = ['B', 'C', 'L']
LINES_SECOND_COLUMN_HTML: List[str] = ['M', 'N', 'O']

# --- Core Logic Class ---
class ProductionRotation:
    """Handles the logic for generating station rotation pairs."""
    def __init__(self) -> None:
        self.lines: List[str] = LINES
        self.stations: List[int] = STATIONS
        self.non_operational_stations: Dict[str, List[int]] = {}
        self.fixed_stations: Dict[str, List[int]] = {}

    def set_non_operational(self, line: str, stations: List[int]) -> None:
        self.non_operational_stations[line] = sorted(list(set(stations)))

    def set_fixed(self, line: str, stations: List[int]) -> None:
        self.fixed_stations[line] = sorted(list(set(stations)))

    def get_operational_stations(self, line: str) -> List[int]:
        non_op_for_line: List[int] = self.non_operational_stations.get(line, [])
        return sorted([s for s in self.stations if s not in non_op_for_line])

    def generate_pairs(self, line: str) -> List[str]:
        pairs: List[str] = []
        if line == 'C':
            fixed_c_stations_input: List[int] = self.fixed_stations.get('C', [])
            valid_fixed_stations_for_pairing: List[int] = [s for s in fixed_c_stations_input if s in self.stations]
            for s_fixed in valid_fixed_stations_for_pairing:
                pairs.append(f"{s_fixed}-{s_fixed}")
            non_op_for_c: List[int] = self.non_operational_stations.get('C', [])
            remaining_for_mirror_pairing_c: List[int] = [
                s for s in self.stations 
                if s not in valid_fixed_stations_for_pairing and s not in non_op_for_c
            ]
            if not remaining_for_mirror_pairing_c and not valid_fixed_stations_for_pairing:
                return [] 
            if remaining_for_mirror_pairing_c: 
                pairs.extend(self.mirror_pair(remaining_for_mirror_pairing_c))
            return pairs
        operational_stations: List[int] = self.get_operational_stations(line)
        if not operational_stations:
            return []
        return self.mirror_pair(operational_stations)

    def mirror_pair(self, stations_to_pair: List[int]) -> List[str]:
        sorted_stations: List[int] = sorted(list(set(stations_to_pair))) 
        pairs: List[str] = []
        n: int = len(sorted_stations)
        for i in range(n // 2):
            pairs.append(f"{sorted_stations[i]}-{sorted_stations[n - 1 - i]}")
        if n % 2 != 0: 
            middle_index: int = n // 2
            pairs.append(f"{sorted_stations[middle_index]}-{sorted_stations[middle_index]}")
        return pairs

    def generate_schedule(self) -> Tuple[str, Dict[str, List[str]]]:
        date_str: str = datetime.now().strftime("%m/%d/%Y")
        schedule_data: Dict[str, List[str]] = {}
        for line_code in self.lines:
            schedule_data[line_code] = self.generate_pairs(line_code)
        return date_str, schedule_data

# --- Session State Management ---
def initialize_session_state() -> None:
    """
    Initializes or resets session state variables, especially on a new day.
    This version performs a daily reset.
    """
    current_date_str: str = datetime.now().strftime("%Y-%m-%d")
    if 'last_date' not in st.session_state or st.session_state.last_date != current_date_str:
        st.session_state.last_date = current_date_str
        # Reset main data structures used by the backend logic
        st.session_state.non_operational = {line: [] for line in LINES} 
        st.session_state.accommodation_c = [] 
        
        # Reset widget-specific keys to ensure fresh defaults for a new day
        for line_code in LINES:
            st.session_state[f"non_op_{line_code}"] = [] 
        st.session_state["accommodation_stations_c"] = [] 

    # Fallback: Ensure essential keys exist if somehow missed by daily reset (e.g., very first session run)
    if 'non_operational' not in st.session_state: # For the logic class
        st.session_state.non_operational = {line: [] for line in LINES}
    if 'accommodation_c' not in st.session_state: # For the logic class
        st.session_state.accommodation_c = []
    
    # For the multiselect widgets themselves
    if "accommodation_stations_c" not in st.session_state:
        st.session_state.accommodation_stations_c = []
    for line_code in LINES:
        if f"non_op_{line_code}" not in st.session_state:
            st.session_state[f"non_op_{line_code}"] = []

def update_session_state_on_submit() -> None:
    """Updates main logic-driving session state variables based on widget inputs."""
    for line_code in LINES:
        st.session_state.non_operational[line_code] = st.session_state.get(f"non_op_{line_code}", [])
    st.session_state.accommodation_c = st.session_state.get("accommodation_stations_c", [])

# --- HTML Generation --- 
def _render_column_html(
    column_lines: List[str], 
    schedule: Dict[str, List[str]], 
    down_stations_data: Dict[str, List[int]]
) -> str:
    """Helper function to render HTML for a single column of lines."""
    column_html = ""
    for line_code in column_lines: 
        column_html += f'<div class="line-group"><div class="line-title">Line {line_code}</div><div class="pairs">'
        has_content_for_line: bool = False 
        if schedule.get(line_code): 
            for pair_text in schedule[line_code]:
                column_html += f'<div class="pair">{pair_text}</div>'
            has_content_for_line = True
        current_line_down_stations: List[int] = down_stations_data.get(line_code, [])
        if current_line_down_stations:
            down_stations_str: str = ', '.join(map(str, sorted(current_line_down_stations)))
            column_html += f'<div class="pair down-station-item">{down_stations_str}</div>'
            has_content_for_line = True 
        if not has_content_for_line: 
             column_html += '<div class="empty-message">No pairs or unavailable stations</div>'
        column_html += '</div></div>' 
    return column_html

def generate_print_friendly_html(date: str, schedule: Dict[str, List[str]], down_stations_data: Dict[str, List[int]]) -> str:
    """Generates the full HTML string for the print-friendly report."""
    css_styles = """
        <style>
            @media print { @page { size: A4; margin: 10mm; } body { margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; } .no-print { display: none !important; } }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: white; color: #1c1c1e; font-size: 10pt; margin: 10mm; line-height: 1.2; position: relative; }
            .container { max-width: 100%; box-sizing: border-box; }
            .header { text-align: center; margin-bottom: 8mm; padding-bottom: 4mm; border-bottom: 1px solid #d1d1d6; }
            .title { font-size: 16pt; font-weight: bold; margin: 0; text-transform: uppercase; color: #1c1c1e; }
            .date { font-size: 10pt; margin: 3mm 0; color: #8e8e93; }
            .columns { display: flex; justify-content: space-between; gap: 8mm; }
            .column { flex: 1; max-width: 48%; }
            .line-group { margin-bottom: 6mm; page-break-inside: avoid; }
            .line-title { font-size: 12pt; font-weight: 600; text-align: center; margin-bottom: 3mm; padding: 2mm 4mm; background-color: #f2f2f7; text-transform: uppercase; color: #1c1c1e; border-radius: 4px; }
            .pairs { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 3mm; padding: 0 2mm; }
            .pair { padding: 3mm 4mm; border: 1px solid #d1d1d6; border-radius: 4px; font-size: 10pt; text-align: center; background-color: white; color: #1c1c1e; }
            .pair.down-station-item { background-color: #fdecea; color: #c0392b; border-color: #c0392b; }
            .empty-message { font-style: italic; color: #8e8e93; text-align: center; padding: 3mm; font-size: 10pt; grid-column: 1 / -1; }
            .watermark { margin-top: 40px; text-align: center; opacity: 0.15; font-size: 12pt; }
        </style>
    """
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Station Rotation - {date}</title>
        {css_styles}
    </head>
    <body>
        <div class='container'>
            <div class='header'> <div class='title'>Station Rotation</div> <div class='date'>Date: {date}</div> </div>
            <div class='columns'>
                <div class='column'>
                    {_render_column_html(LINES_FIRST_COLUMN_HTML, schedule, down_stations_data)}
                </div>
                <div class='column'>
                    {_render_column_html(LINES_SECOND_COLUMN_HTML, schedule, down_stations_data)}
                </div>
            </div>
        </div>
        <div class='watermark'>
            <img src='https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg' alt='Amazon Logo' style='height: 30px; vertical-align: middle;'>
            <div style='margin-top: 4px;'>jerjerry</div>
        </div>
    </div></body></html>"""
    return html_content

# --- UI Rendering Helper Functions ---
def _render_line_input_row(
    primary_label_text: str, 
    secondary_label_text: str,
    widget_key: str,
    options: List[int],
    help_text: str,
    col_widths: List[int] = [2,5], 
    is_line_c_unavailable: bool = False, 
    all_stations: Optional[List[int]] = None 
    ) -> None:
    """Helper function to render a two-column input row for a line."""
    col_label, col_widget = st.columns(col_widths)
    with col_label:
        if primary_label_text: 
            st.markdown(f"**{primary_label_text}**<br>{secondary_label_text}", unsafe_allow_html=True)
        else:
            st.markdown(f"{secondary_label_text}", unsafe_allow_html=True) # For Line C's second input
            
    with col_widget:
        widget_options = options
        if is_line_c_unavailable and all_stations is not None:
            currently_accommodated_c: List[int] = st.session_state.get("accommodation_stations_c", [])
            widget_options = [s for s in all_stations if s not in currently_accommodated_c]
            
            if not widget_options:
                if currently_accommodated_c:
                    st.info(f"All stations are 'Accommodated' or no others to mark 'Unavailable'.")
                else:
                    st.warning(f"No stations to mark as 'Unavailable'.")
                return 

        st.multiselect(
            label="", # Visual label is in the left column
            options=widget_options,
            key=widget_key, 
            help=help_text
        )

# --- Main Application UI and Logic Flow ---
def render_configuration_form(all_stations_for_multiselect: List[int]) -> bool:
    """Renders the main configuration form and returns the submission status."""
    with st.form(key="station_config_form", clear_on_submit=False):
        st.header("Station Configuration")
        st.caption("Specify unavailable stations and Line C accommodations.")
        st.markdown("---") 

        col_widths = [2, 5] 

        for line_key in LINES: 
            if line_key == 'C':
                _render_line_input_row(
                    primary_label_text="Line C",
                    secondary_label_text="Accommodations",
                    widget_key="accommodation_stations_c",
                    options=all_stations_for_multiselect,
                    help_text="Select stations for operators who will remain at their current station (e.g., for '1-1' type pairings)."
                )
                _render_line_input_row(
                    primary_label_text="", # No primary label for the second Line C input
                    secondary_label_text="Unavailable",
                    widget_key=f"non_op_{line_key}",
                    options=all_stations_for_multiselect, 
                    help_text="Select stations on Line C that are broken or cannot be used today. Cannot be an accommodated station.",
                    is_line_c_unavailable=True,
                    all_stations=all_stations_for_multiselect
                )
            else: 
                _render_line_input_row(
                    primary_label_text=f"Line {line_key}",
                    secondary_label_text="Unavailable",
                    widget_key=f"non_op_{line_key}",
                    options=all_stations_for_multiselect,
                    help_text=f"Select stations on Line {line_key} that are broken or cannot be used today."
                )
            st.write("") # Consistent vertical gap

        st.divider() 
        
        submitted: bool = st.form_submit_button(
            "Generate & Download Schedule", 
            type="primary",
            use_container_width=True,
            on_click=update_session_state_on_submit 
        )
    return submitted

def validate_line_c_configuration() -> bool:
    """Validates Line C selections for overlap. Returns True if valid, False otherwise."""
    final_accommodated_c_stations: Set[int] = set(st.session_state.accommodation_c)
    final_unavailable_c_stations: Set[int] = set(st.session_state.non_operational.get('C', []))
    common_stations_error_check: Set[int] = final_accommodated_c_stations.intersection(final_unavailable_c_stations)

    if common_stations_error_check:
        st.error(
            f"Configuration Error for Line C: Station(s) {', '.join(map(str, sorted(list(common_stations_error_check))))} "
            f"cannot be selected in both 'Accommodations' and 'Unavailable'. "
            f"Please adjust your selections for Line C and try again."
        )
        return False
    return True

def render_download_section(
        rotation_logic_handler: ProductionRotation, 
        current_date_display: str, 
        schedule_data: Dict[str, List[str]]
    ) -> None:
    """Renders the download button and success/info messages."""
    down_stations_for_html: Dict[str, List[int]] = rotation_logic_handler.non_operational_stations 
    has_any_pairs: bool = any(schedule_data.values())
    has_any_down_stations: bool = any(down_stations_for_html.values())

    if not has_any_pairs and not has_any_down_stations:
        st.error("No operational stations for pairs and no unavailable stations selected. Cannot generate a meaningful schedule.")
        return 
    elif not has_any_pairs and has_any_down_stations:
         st.info("No operational stations available for pairing. The report will show only the unavailable stations.")
    
    html_content: str = generate_print_friendly_html(current_date_display, schedule_data, down_stations_for_html)
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


def main() -> None:
    st.set_page_config(page_title="Station Rotation", layout="wide")
    st.title("Station Rotation")

    initialize_session_state() 
    
    rotation_logic_handler = ProductionRotation() 
    all_stations_for_multiselect: List[int] = STATIONS 

    # No "Clear All Selections" button in this version, relies on daily reset
    # Informational message if it's a new day and form might have old data (if session persisted unexpectedly)
    current_date_str_for_display = datetime.now().strftime("%Y-%m-%d")
    if 'last_date' in st.session_state and st.session_state.last_date != current_date_str_for_display:
        # This condition implies initialize_session_state should have cleared inputs.
        # If inputs are *not* clear, it means session persisted across days unexpectedly.
        # The current initialize_session_state logic is designed to clear on new day.
        st.info(
             f"Welcome! It's a new day ({current_date_str_for_display}). "
             f"The form has been reset for today's input."
        )


    submitted = render_configuration_form(all_stations_for_multiselect)

    if submitted:
        if not validate_line_c_configuration():
            return 

        st.header("Download")
        for line_code in LINES: 
            rotation_logic_handler.set_non_operational(line_code, st.session_state.non_operational.get(line_code, []))
        rotation_logic_handler.set_fixed('C', st.session_state.accommodation_c)

        current_date_display, schedule_data = rotation_logic_handler.generate_schedule()
        render_download_section(rotation_logic_handler, current_date_display, schedule_data)
        
    # Display initial prompt if not submitted and not a "new day" message scenario
    elif 'last_date' not in st.session_state or \
         (st.session_state.get('last_date') == current_date_str_for_display and not submitted):
        st.info("Configure station settings using the form above and click 'Generate & Download Schedule'.")


if __name__ == "__main__":
    main()
