# Rotator - Production Line Rotation System

A streamlined tool for managing and generating production line rotation schedules.

## Features

- Generate rotation schedules for multiple production lines
- Handle non-operational stations
- Manage accommodation stations for Line C
- Clean, professional print layout
- Amazon-style dark theme

## How to Use

1. **Launch the Application**
   - Run the application using Streamlit
   - The main interface will appear with all available production lines

2. **Configure Production Lines**
   - For each production line (B, C, L, M, N, O):
     - Click on the line expander to reveal its settings
     - Select non-operational stations using the multiselect box
     - For Line C only:
       - Check "Accommodation Stations?" if needed
       - Select accommodation stations using the multiselect box

3. **Generate Schedule**
   - After configuring all necessary lines
   - Click "Generate Schedule" button
   - The rotation schedule will be displayed with a clean print layout

4. **Print Schedule**
   - The schedule is automatically formatted for printing
   - Use your browser's print function to print the schedule
   - The layout is optimized for A4 paper with minimal ink usage

## Layout Structure

- **Header**
  - Application title "Rotator"
  - Current date

- **Production Lines**
  - Lines are split into two columns for better space utilization
  - Each line shows its rotation pairs
  - Accommodation stations for Line C are clearly marked

## Technical Details

- Built with Python and Streamlit
- Uses HTML/CSS for print-friendly layout
- Optimized for A4 paper printing
- Responsive design for both screen and print

## Requirements

- Python 3.x
- Streamlit
- Modern web browser with printing capabilities

## License

Copyright © 2025 Jerry Jerz, JERZ. All Rights Reserved.

This program is the property of Jerry Jerz and JERZ.  
Unauthorized copying, redistribution, modification, or use of this program, in whole or in part, is strictly prohibited without prior written consent from the creator.  

This software is licensed for internal use only.  
Any other use requires explicit written permission from Jerry Jerz / JERZ.
