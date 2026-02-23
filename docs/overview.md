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

There are 10 scripts (list above).
There are 16 datasets {Dx}.
There are 2 results {Rx}.

There will be additional scripts that show the validity of some of the steps:
- Plot comparrison the FFT-apmlitudes of two weeks to show certain period ranges has been dampend.
- Plot comparing a unmodified FFT-apmlitudes, a modified FFT-apmlitudes, and the average FFT-apmlitudes pre cutoff.
- Animation showing how sines can reprocude measured frequency.
- Plot comparring measured frequency, frequency signal from FFT, and frequency signal from modified FFT.