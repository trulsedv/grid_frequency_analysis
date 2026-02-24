1. Download frequency archives
    - -> monthly .7z/.zip {D1}
2. Extract frequency archives
    - monthly .7z/.zip -> daily 10 Hz .csv {D2}
3. Create weekly 1 Hz frequency logs (quality check, fill/reject, update quality report)
    - daily 10 Hz .csv -> weekly 1 Hz .csv {D3} & quality report .csv {R1}
4. Calculate weekly STFT (FFT per window)
    - weekly 1 Hz .csv -> weekly STFT .csv {D4} (column per window, row per period, value complex)
5. Calculate average amplitude over the windows per week
    - weekly STFT .csv -> weekly amplitudes .csv {D5}
6. Calcaulte average amplitudes before cutoff
    - weekly amplitudes .csv -> ampltidues pre cutoff .csv {D6} (one file)
7. Modify 2025 FFTs
    - IN: weekly STFT .csv & ampltidues pre cutoff .csv
    - OUT:
        - modified 2025 weekly STFT .csv (all periods) {D7}
        - modified 2025 weekly STFT .csv (low and high periods) {D8}
        - modified 2025 weekly STFT .csv (low periods) {D9}
8. Calculate frequency signal from modified FFTs
    - IN:
        - modified 2025 weekly STFT .csv (all periods)
        - modified 2025 weekly STFT .csv (low and high periods)
        - modified 2025 weekly STFT .csv (low periods)
    - OUT:
        - modified 2025 weekly 1 Hz .csv  (all periods) {D10}
        - modified 2025 weekly 1 Hz .csv  (low and high periods) {D11}
        - modified 2025 weekly 1 Hz .csv  (low periods) {D12}
9. Calculate minutes outside normal band
    - IN:
        - weekly 1 Hz .csv
        - modified 2025 weekly 1 Hz .csv  (all periods)
        - modified 2025 weekly 1 Hz .csv  (low and high periods)
        - modified 2025 weekly 1 Hz .csv  (low periods)
    - OUT:
        - minutes outside norm .csv (all unmodified weeks) {D13}
        - minutes outside norm .csv (modified 2025 weeks all periods) {D14}
        - minutes outside norm .csv (modified 2025 weeks low and high periods) {D15}
        - minutes outside norm .csv (modified 2025 weeks low periods) {D16}
10. Plot minutes outside norm
    - IN:
        - minutes outside norm .csv (all unmodified weeks)
        - minutes outside norm .csv (modified 2025 weeks all periods)
        - minutes outside norm .csv (modified 2025 weeks low and high periods)
        - minutes outside norm .csv (modified 2025 weeks low periods)
    - OUT:
        - figure of cumulative minutes outside norm per year (including modified years) {R2}
            - showing years prior to 2025 as grey lines (not in legend but with lines are labeled)
            - showing 2025 as black line
            - showing modified 2025 (all periods) as red line
            - showing area between 2025 and modifed 2025 (low periods) as blue area
            - showing area between modifed 2025 (low periods) and modified 2025 (low and high periods) as red area
            - showing area between modified 2025 (low and high periods) and modified 2025 (all periods) as grey area

All scripts, datasets, and results have been described above or below in the appendecies. There shouold not be more files except utils.py and the necessary files in root.
The scripts, datasets, and results should have short and understandable names including the numberscheme that refer to the readme.

The readme should be a short "scientific report" (as short as possible), and a quick intro to use the scripts. It should be feasible for an engineer to understand and make him/her be able to understand the result and critize the method of the analyzis.
The final plot show that the reduction in minutes outside norm is mostly because of dampening of high period oscilation (balancing periods), but also significanlty by dampening of low period oscilations (frequency controll periods). This indicate that improved balancing is probably the main cause of the reduction, but improved frequency control has contributed a significant part.

The datasets should not be pushed to github.

This should the only file in the docs folder.

Appendecies

4a. Animate adding sines to fitt the frequency of the first hour of 2025W22
    - IN: weekly 1 Hz .csv {D3} & weekly STFT .csv {D4}
    - OUT: animation {Ra1}
5a. Plot FFT-amplitudes (D5, average for windows) of W22 in 2025 and 2024
    - IN: weekly amplitudes .csv {D5}
    - OUT: figure showing FFT-amplitudes {Ra2}
        - both x-axis and y-axis should be log
5b. Calculate the average ampltidue per week for each defined bin
    - IN: weekly amplitudes .csv {D5}
    - OUT: bined ampltidues .csv {Da1} (columns bins, rows weeks, values average ampltidue (in bin all windows))
5c. Plot the average ampltitudes
    - IN: bined ampltidues .csv {Da1}
    - OUT: figure showing the amplitude of the bins over time {Ra3}
        - y-axis should be log
6a. Modify the weekly amplitudes
    - IN: weekly amplitudes .csv {D5} & ampltidues pre cutoff .csv {D6}
    - OUT: modified weekly amplitudes .csv (Da2)
6b. Plot unmodified and modified weekly amplitudes, and ampltidues pre cutoff
    - IN: weekly amplitudes .csv {D5} & modified weekly amplitudes .csv (Da2) & ampltidues pre cutoff .csv {D6}
    - OUT: figure showing FFT-amplitudes {Ra4}
        - both x-axis and y-axis should be log
8a. Calculate frequency signal for 2025W22 from FFTs
    - IN: weekly STFT .csv {D4}
    - OUT: reproduced weekly 1 Hz .csv {Da3}
8b. Plot 2025W22 measured, reproduced from SFTF, and reproduced from modifed SFTF
    - IN: weekly 1 Hz .csv {D3} & reproduced weekly 1 Hz .csv {Da3} & modified 2025 weekly 1 Hz .csv  (low and high periods) {D11}
    - OUT: figure showing the frequency signals {Ra5}
        - all lines should be a bit transparent since they will be on top of eachother a lot
        - figure should only show 1 hour to make details clearer