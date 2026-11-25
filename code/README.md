# Code for the MapleStory world creation-restriction study

메이플스토리 월드별 신규 캐릭터 생성 제한 해제(2024년 1월 12일)를 분석한 연구의 자료 수집 코드와 분석 코드입니다.

This folder holds the data collection notebooks and the analysis scripts for a difference-in-differences study of the lift of new character creation restrictions on two MapleStory worlds (Scania and Luna) on January 12, 2024.

## Contents

```
code/
├── collection/      Google Colab notebooks that collect the sample from the NEXON Open API
│   ├── 01_collection_five_worlds.ipynb
│   └── 02_collection_remaining_worlds_and_early_sample.ipynb
├── analysis/        Python scripts that produce every estimate, table and figure input
│   ├── 01_main_analysis.py           Poisson DID, substitute-world models, Reboot models,
│   │                                 permutation tests, event study (current and early samples)
│   ├── 02_trends_event_study.py      World-specific linear trends, event study against large
│   │                                 and small comparison worlds, World Leap window excluded
│   ├── 03_level_bands_placebo.py     Estimates by current level band, placebo lift dates,
│   │                                 world-clustered standard errors
│   ├── 04_robustness_extra.py        Sample flow, unconfirmed characters included, split at
│   │                                 January 25, two-sided and large-world permutation tests
│   ├── 05_confirmation_rate.py       Confirmation rate of creation world by week and group
│   ├── 06_lift_day.py                Relative creation on the lift date and the day after
│   ├── 07_figure2_data.py            Weekly average creation index behind Fig. 2
│   ├── 08_tables.py                  Builds the result tables from the saved estimates
│   ├── 09_middle_estimate.py         Main model excluding only the treated worlds' excess of
│   │                                 unconfirmed characters (by creation week), with permutation test
│   └── 10_unconfirmed_levels.py      Current-level distribution of unconfirmed characters by group and period
└── requirements.txt
```

## Data

The data are not included in this repository. They were collected from the NEXON Open API (https://openapi.nexon.com) with the notebooks in `collection/`, which need an API key issued by NEXON. The notebooks store no character names, identifiers, ranks or page numbers; levels are stored in bands of ten.

Each notebook writes one CSV file per world and ranking date, named `records_<ranking date>_<world>.csv`, with these columns: `rank_date`, `world`, `cluster` (anonymised ranking page), `status`, `same_world`, `date_create`, `world_first_seen`, `date_first_seen`, `level_band_rank`, `level_band_now`.

The analysis scripts expect this layout:

```
data/
├── maple_main_v4/records_2026-10-28_<world>.csv    five worlds, ranking of 2026-10-28
└── maple_main_v5/records_2026-10-28_<world>.csv    remaining worlds, ranking of 2026-10-28
    maple_main_v5/records_2024-11-06_<world>.csv    all worlds, ranking of 2024-11-06 (early sample)
```

Because rankings change every day and the API serves about two years of history, a new collection will not return the same sample.

## Running the analysis

The analysis was run with Python 3.14 and the package versions in `requirements.txt`.

```
cd code/analysis
export MAPLE_DATA=/path/to/data/     # folder that holds maple_main_v4 and maple_main_v5 (default ./data/)
export MAPLE_OUT=./                  # where result files are written (default: current folder)
python 01_main_analysis.py           # writes results_v5.json
python 02_trends_event_study.py      # writes results_v5b.json
python 03_level_bands_placebo.py     # writes results_v5c.json
python 04_robustness_extra.py        # writes results_review.json
python 05_confirmation_rate.py
python 06_lift_day.py
python 07_figure2_data.py            # writes fig2.json
python 08_tables.py                  # reads the four result files, writes tables_md.json
python 09_middle_estimate.py         # writes results_middle.json
python 10_unconfirmed_levels.py
```

Scripts 02 to 07 load the shared functions from `01_main_analysis.py`, so run them from the `analysis` folder. Standard errors and intervals come from a bootstrap over ranking pages with 999 replications (random seed fixed in script 01), so scripts 01 to 04 take a while to finish.

## Note on the use of generative AI

The code for data collection and analysis was written with the help of a generative AI tool (Claude, Anthropic). The researcher reviewed the code and the results.
