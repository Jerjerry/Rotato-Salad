import streamlit as st
from datetime import datetime
import io
from typing import List, Dict, Tuple, Any, Set, Optional # Added for type hinting

# --- Configuration Constants ---
LINES: List[str] = ['B', 'C', 'L', 'M', 'N', 'O']
STATIONS: List[int] = list(range(1, 21))
LINES_FIRST_COLUMN: List[str] = ['B', 'C', 'L']
LINES_SECOND_COLUMN: List[str] = ['M', 'N', 'O']

# --- Core Logic Class ---
class ProductionRotation:
    """Handles the logic for generating station rotation pairs."""
    def __init__(self) -> None:
        self.lines: List[str] = LINES
        self.stations: List[int] = STATIONS
        self.non_operational_stations: Dict[str, List[int]] = {}
        self.fixed_stations: Dict[str, List[int]] = {}

    def set_non_operational(self, line: str, stations: List[int]) -> None:
        """Sets the non-operational stations for a given line."""
        self.non_operational_stations[line] = sorted(list(set(stations))) # Ensure unique and sorted

    def set_fixed(self, line: str, stations: List[int]) -> None:
        """Sets the fixed (accommodated) stations for a given line."""
        self.fixed_stations[line] = sorted(list(set(stations))) # Ensure unique and sorted

    def get_operational_stations(self, line: str) -> List[int]:
        """Gets the list of operational stations for a line, excluding non-operational ones."""
        temp_non_operational: List[int] = self.non_operational_stations.get(line, [])
        # Using a set for faster lookups if self.stations were very large, but for N=20, list is fine.
        # For clarity and consistency with current small scale, keeping list comprehension as is.
        return sorted([s for s in self.stations if s not in temp_non_operational])

    def generate_pairs(self, line: str) -> List[str]:
        """Generates station rotation pairs for a given line."""
        operational: List[int] = self.get_operational_stations(line)
        if not operational:
            return []

        if line == 'C':
            fixed_c_stations: List[int] = self.fixed_stations.get(line, [])
            # Ensure fixed stations are actually operational (e.g., not also marked as down)
            valid_fixed: List[int] = [s for s in fixed_c_stations if s in operational]
            fixed_pairs: List[str] = [f"{s}-{s}" for s in valid_fixed]
            
            # Stations available for mirror pairing are operational ones not in valid_fixed
            remaining_for_pairing: List[int] = [s for s in operational if s not in valid_fixed]
            return fixed_pairs + self.mirror_pair(remaining_for_pairing)
        
        return self.mirror_pair(operational)

    def mirror_pair(self, stations_to_pair: List[int]) -> List[str]:
        """Creates mirrored pairs from a list of stations."""
        # Ensure stations are sorted before pairing for consistent output
        sorted_stations: List[int] = sorted(list(set(stations_to_pair))) # Ensure unique and sorted
        pairs: List[str] = []
        n: int = len(sorted_stations)
        for i in range(n // 2):
            pairs.append(f"{sorted_stations[i]}-{sorted_stations[n - 1 - i]}")
        if n % 2 != 0: # If odd number of stations, middle one pairs with itself
            middle_index: int = n // 2
            pairs.append(f"{sorted_stations[middle_index]}-{sorted_stations[middle_index]}")
        return pairs

    def generate_schedule(self) -> Tuple[str, Dict[str, List[str]]]:
        """Generates the full rotation schedule for all lines."""
        date_str: str = datetime.now().strftime("%m/%d/%Y")
        schedule_data: Dict[str, List[str]] = {}
        for line_code in self.lines:
            schedule_data[line_code] = self.generate_pairs(line_code)
        return date_str, schedule_data

# --- Session State Management ---
def initialize_session_state() -> None:
    """Initializes or resets session state variables, especially on a new day."""
    current_date_str: str = datetime.now().strftime("%Y-%m-%d")
    
    if 'last_date' not in st.session_state or st.session_state.last_date != current_date_str:
        st.session_state.last_date = current_date_str
        # Reset daily data by re-assigning
        st.session_state.non_operational = {line: [] for line in LINES}
        st.session_state.accommodation_c = []
        st.session_state.has_accommodation_c = False # Explicitly reset this flag
        # Clean up old individual line keys if they were used differently before (optional, but safer if keys changed)
        for line in LINES:
            if f"non_op_{line}" in st.session_state: # Check before popping
                 st.session_state[f"non_op_{line}"] = [] # Reset individual widget defaults
        if "accommodation_stations_c" in st.session_state: # Check before popping
            st.session_state["accommodation_stations_c"] = [] # Reset widget default

    # Ensure essential keys exist if it's the very first run or after a full clear
    # This part is mostly for the very first run of the session
    if 'non_operational' not in st.session_state:
        st.session_state.non_operational = {line: [] for line in LINES}
    if 'accommodation_c' not in st.session_state:
        st.session_state.accommodation_c = []
    if 'has_accommodation_c' not in st.session_state:
        st.session_state.has_accommodation_c = False


def update_session_state_on_submit() -> None:
    """Updates session state based on form inputs."""
    for line in LINES:
        st.session_state.non_operational[line] = st.session_state.get(f"non_op_{line}", [])
    
    accommodated_stations: List[int] = st.session_state.get("accommodation_stations_c", [])
    st.session_state.accommodation_c = accommodated_stations
    st.session_state.has_accommodation_c = len(accommodated_stations) > 0

# --- HTML Generation ---
# (This function's output format is fixed as per your request)
def generate_print_friendly_html(date: str, schedule: Dict[str, List[str]], down_stations_data: Dict[str, List[int]]) -> str:
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
            
            .pair {{ 
                padding: 3mm 4mm; 
                border: 1px solid #d1d1d6; 
                border-radius: 4px; 
                font-size: 10pt; 
                text-align: center; 
                background-color: white; 
                color: #1c1c1e; 
            }}
            
            .pair.down-station-item {{
                background-color: #fdecea; 
                color: #c0392b;            
                border-color: #c0392b;     
            }}

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
    # Using the global constants for column line assignments
    for line_code in LINES_FIRST_COLUMN:
        html += f'<div class="line-group"><div class="line-title">Line {line_code}</div><div class="pairs">'
        has_content: bool = False
        if schedule.get(line_code):
            for pair_text in schedule[line_code]:
                html += f'<div class="pair">{pair_text}</div>'
            has_content = True
        
        current_line_down_stations: List[int] = down_stations_data.get(line_code, [])
        if current_line_down_stations:
            down_stations_str: str = ', '.join(map(str, sorted(current_line_down_stations)))
            html += f'<div class="pair down-station-item">{down_stations_str}</div>'
            has_content = True
        
        if not has_content:
             html += '<div class="empty-message">No pairs or unavailable stations</div>'
        
        html += '</div></div>' 
    html += '</div><div class="column">'

    for line_code in LINES_SECOND_COLUMN:
        html += f'<div class="line-group"><div class="line-title">Line {line_code}</div><div class="pairs">'
        has_content = False
        if schedule.get(line_code):
            for pair_text in schedule[line_code]:
                html += f'<div class="pair">{pair_text}</div>'
            has_content = True

        current_line_down_stations = down_stations_data.get(line_code, [])
        if current_line_down_stations:
            down_stations_str = ', '.join(map(str, sorted(current_line_down_stations)))
            html += f'<div class="pair down-station-item">{down_stations_str}</div>'
            has_content = True
            
        if not has_content:
            html += '<div class="empty-message">No pairs or unavailable stations</div>'
        
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
def main() -> None:
    st.set_page_config(page_title="Station Rotation", layout="wide")
    st.title("Station Rotation")

    initialize_session_state()
    
    rotation = ProductionRotation() 
    # STATIONS constant is used by rotation object internally
    # LINES constant is used for iterating here and by rotation object.

    with st.form(key="station_config_form", clear_on_submit=False):
        st.header("Station Configuration")
        st.subheader("Temporarily Unavailable Stations")
        st.caption("Select stations temporarily unavailable for today on each line.")

        for line_key in LINES: 
            # All stations are potentially available for selection in multiselect
            all_stations_for_multiselect: List[int] = STATIONS 

            if line_key == 'C':
                # Get default accommodated stations from session state for the widget
                default_accommodated_c: List[int] = st.session_state.get("accommodation_c", [])
                accommodated_stations_c: List[int] = st.multiselect(
                    "Line C Accommodations",
                    options=all_stations_for_multiselect,
                    default=default_accommodated_c,
                    key="accommodation_stations_c", # This key directly updates st.session_state.accommodation_c via on_click
                    help="Select the specific station(s) that require accommodation on Line C today."
                )

                # Stations available to be marked as down are those not selected for accommodation
                available_for_down_c: List[int] = [s for s in all_stations_for_multiselect if s not in st.session_state.get("accommodation_stations_c", [])]
                
                # Get default non-operational for Line C for the widget
                default_non_op_c: List[int] = st.session_state.non_operational.get(line_key, [])

                if available_for_down_c:
                    st.multiselect(
                        f"Line {line_key} (Unavailable)", # Changed label
                        options=available_for_down_c, # Only show stations not accommodated
                        default=[s for s in default_non_op_c if s in available_for_down_c], # Ensure default is valid
                        key=f"non_op_{line_key}",
                        help=f"Select stations temporarily unavailable today on Line {line_key} (excluding accommodated stations)."
                    )
                elif st.session_state.get("accommodation_stations_c", []): # If only accommodated stations or no other stations left
                     st.info(f"All selectable stations on Line {line_key} may be accommodated or no other stations available to mark as unavailable.")
                else: # No stations available at all for down selection (e.g. if STATIONS was empty)
                    st.warning(f"No stations available to mark as unavailable for Line {line_key}.")

            else: # For lines other than C
                default_non_op_line: List[int] = st.session_state.non_operational.get(line_key, [])
                st.multiselect(
                    f"Line {line_key} (Unavailable)", # Changed label
                    options=all_stations_for_multiselect,
                    default=default_non_op_line,
                    key=f"non_op_{line_key}",
                    help=f"Select stations temporarily unavailable today on Line {line_key}."
                )
        st.divider()
        submitted: bool = st.form_submit_button(
            "Generate & Download",
            on_click=update_session_state_on_submit, # Updates session state before the rest of this block runs
            type="primary",
            use_container_width=True
        )

    if submitted:
        st.header("Download")
        # Populate the rotation object using the (now updated by on_click) session state
        for line_code in LINES: 
            rotation.set_non_operational(line_code, st.session_state.non_operational.get(line_code, []))
        rotation.set_fixed('C', st.session_state.accommodation_c) # Use updated session state for accommodations

        current_date_display, schedule_data = rotation.generate_schedule()
        
        # This is the dictionary of down stations for each line, from the rotation object
        down_stations_for_html: Dict[str, List[int]] = rotation.non_operational_stations 

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

    elif 'last_date' not in st.session_state: # First run, or session state cleared
        st.info("Configure station settings using the form above and click 'Generate & Download'.")

if __name__ == "__main__":
    main()
