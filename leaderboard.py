import base64
import html
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import os


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        str(BASE_DIR),
    )
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATA_FILE = DATA_DIR / "leaderboard_data.json"

POSITION_ASSETS_DIR = BASE_DIR / "assets" / "positions"
UI_ASSETS_DIR = BASE_DIR / "assets" / "ui"

RANKING_STARS_PATH = UI_ASSETS_DIR / "ranking-stars.png"

MAX_PLAYERS = 8


# =========================================================
# DATA
# =========================================================

def default_data() -> dict:
    return {
        "players": [
            {"id": 1, "name": "Franklin", "total": 0},
            {"id": 2, "name": "Red", "total": 0},
            {"id": 3, "name": "Josh", "total": 0},
            {"id": 4, "name": "Gabe", "total": 0},
        ],
        "history": [],
        "next_player_id": 5,
    }


def save_data(data: dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


def normalize_data(data: dict) -> dict:
    data.setdefault("players", [])
    data.setdefault("history", [])

    highest_id = 0

    for player in data["players"]:
        player.setdefault("id", highest_id + 1)
        player.setdefault("name", "Unknown")
        player.setdefault("total", 0)

        player["id"] = int(player["id"])
        player["total"] = int(player["total"])

        highest_id = max(
            highest_id,
            player["id"],
        )

    stored_next_id = int(
        data.get(
            "next_player_id",
            highest_id + 1,
        )
    )

    data["next_player_id"] = max(
        stored_next_id,
        highest_id + 1,
    )

    return data


def load_data() -> dict:
    if not DATA_FILE.exists():
        data = default_data()
        save_data(data)
        return data

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return normalize_data(data)

    except (
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
    ):
        st.error(
            "The data file could not be read. "
            "A new leaderboard was created."
        )

        data = default_data()
        save_data(data)

        return data


def get_player(
    data: dict,
    player_id: int,
) -> dict | None:
    for player in data["players"]:
        if player["id"] == player_id:
            return player

    return None


def get_latest_week_score(
    data: dict,
    player_id: int,
) -> int:
    if not data["history"]:
        return 0

    latest_entry = data["history"][-1]

    for score in latest_entry.get("scores", []):
        if int(score.get("player_id", -1)) == player_id:
            return int(score.get("tickets", 0))

    return 0


def get_previous_ranking(
    data: dict,
) -> dict[int, int]:
    if not data["history"]:
        return {}

    latest_entry = data["history"][-1]

    latest_scores = {
        int(score["player_id"]): int(
            score.get("tickets", 0)
        )
        for score in latest_entry.get("scores", [])
    }

    previous_totals = {}

    for player in data["players"]:
        previous_totals[player["id"]] = (
            int(player["total"])
            - latest_scores.get(player["id"], 0)
        )

    previous_order = sorted(
        data["players"],
        key=lambda player: (
            -previous_totals[player["id"]],
            player["id"],
        ),
    )

    return {
        player["id"]: position
        for position, player in enumerate(
            previous_order,
            start=1,
        )
    }


# =========================================================
# IMAGE AND HTML HELPERS
# =========================================================

def render_html(content: str) -> None:
    """
    Converts multiline HTML into one compact line so
    Streamlit does not treat indented HTML as code.
    """

    compact_html = " ".join(
        line.strip()
        for line in content.splitlines()
        if line.strip()
    )

    st.markdown(
        compact_html,
        unsafe_allow_html=True,
    )


def file_to_data_uri(
    path: Path,
) -> str | None:
    if not path.exists():
        return None

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }

    mime_type = mime_types.get(
        path.suffix.lower()
    )

    if mime_type is None:
        return None

    encoded = base64.b64encode(
        path.read_bytes()
    ).decode("utf-8")

    return (
        f"data:{mime_type};"
        f"base64,{encoded}"
    )


def get_rank_icon_html(
    position: int,
) -> str:
    """
    Positions 1–5 use custom images.
    Positions 6–8 use a numbered fallback.
    """

    icon_path = (
        POSITION_ASSETS_DIR
        / f"{position}.png"
    )

    data_uri = file_to_data_uri(
        icon_path
    )

    if data_uri is not None:
        return (
            '<img '
            'class="rank-icon-image" '
            f'src="{data_uri}" '
            f'alt="Position {position}">'
        )

    return (
        '<div class="rank-fallback">'
        f"#{position}"
        "</div>"
    )


def get_ranking_stars_html() -> str:
    data_uri = file_to_data_uri(
        RANKING_STARS_PATH
    )

    if data_uri is None:
        return ""

    return (
        '<img '
        'class="ranking-stars-image" '
        f'src="{data_uri}" '
        'alt="Ranking stars">'
    )


# =========================================================
# TOPOGRAPHIC BACKGROUND
# =========================================================

def create_topographic_background() -> str:
    svg = """
    <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 1600 1000"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
    >
        <rect
            width="1600"
            height="1000"
            fill="transparent"
        />

        <g
            stroke="#58d5ff"
            stroke-width="1.15"
            stroke-opacity="0.15"
            fill="none"
        >
            <path d="M-160 105 C40 -45 245 -15 365 120 C480 248 390 390 210 408 C20 425 -155 300 -160 105 Z"/>
            <path d="M-115 125 C45 5 215 20 315 135 C408 242 335 345 190 360 C35 375 -105 275 -115 125 Z"/>
            <path d="M-65 145 C55 55 185 62 260 150 C330 232 275 302 165 315 C48 327 -55 252 -65 145 Z"/>
            <path d="M-18 165 C70 102 158 105 212 170 C265 232 220 270 140 278 C60 287 -5 235 -18 165 Z"/>

            <path d="M1040 -80 C1260 -160 1505 -50 1640 130 C1770 305 1640 475 1410 470 C1185 465 985 305 1000 105 C1006 28 1018 -25 1040 -80 Z"/>
            <path d="M1090 -25 C1275 -90 1475 -5 1585 142 C1690 285 1585 420 1398 415 C1215 410 1050 280 1063 120 C1068 63 1078 16 1090 -25 Z"/>
            <path d="M1145 30 C1290 -20 1445 45 1530 158 C1610 266 1530 365 1387 360 C1247 355 1122 257 1130 135 C1134 92 1138 58 1145 30 Z"/>
            <path d="M1200 82 C1305 48 1415 94 1475 174 C1533 250 1475 310 1375 308 C1272 305 1188 235 1190 153 C1192 124 1195 100 1200 82 Z"/>

            <path d="M390 320 C530 180 785 155 960 290 C1125 420 1095 635 920 745 C740 858 475 805 355 625 C285 520 300 410 390 320 Z"/>
            <path d="M430 350 C548 235 758 215 905 325 C1042 428 1018 602 873 692 C725 785 510 742 408 592 C350 505 360 422 430 350 Z"/>
            <path d="M475 380 C570 290 730 275 850 360 C960 440 942 572 827 642 C708 716 545 680 462 565 C415 498 422 438 475 380 Z"/>
            <path d="M520 412 C590 350 705 338 795 402 C878 462 865 545 780 598 C692 650 575 625 515 545 C480 497 485 452 520 412 Z"/>

            <path d="M-130 690 C60 550 300 555 445 720 C580 875 470 1045 250 1080 C20 1115 -165 935 -130 690 Z"/>
            <path d="M-80 720 C75 605 270 612 388 745 C498 870 410 998 232 1025 C48 1053 -108 910 -80 720 Z"/>
            <path d="M-28 748 C90 662 242 667 330 770 C414 865 345 955 215 975 C78 995 -48 890 -28 748 Z"/>
            <path d="M25 775 C110 715 215 718 278 790 C336 858 290 916 198 930 C103 944 10 870 25 775 Z"/>

            <path d="M1015 675 C1170 520 1435 525 1595 690 C1745 845 1640 1045 1405 1080 C1168 1115 950 940 1015 675 Z"/>
            <path d="M1065 705 C1195 580 1410 585 1538 718 C1655 838 1570 992 1388 1020 C1200 1048 1018 908 1065 705 Z"/>
            <path d="M1115 735 C1215 642 1380 647 1480 748 C1570 840 1508 945 1370 967 C1228 988 1082 880 1115 735 Z"/>
            <path d="M1168 765 C1240 700 1358 702 1425 775 C1488 840 1445 900 1355 913 C1260 928 1148 862 1168 765 Z"/>
        </g>

        <g
            stroke="#277cff"
            stroke-width="1.35"
            stroke-opacity="0.07"
            fill="none"
        >
            <path d="M-120 510 C170 365 330 625 610 480 C870 345 1110 555 1340 430 C1460 365 1540 380 1680 470"/>
            <path d="M-100 560 C180 420 350 680 625 535 C885 400 1125 610 1355 485 C1470 420 1560 435 1680 525"/>
            <path d="M240 -30 C360 135 520 120 640 -10"/>
            <path d="M820 1010 C950 850 1110 870 1230 1035"/>
        </g>
    </svg>
    """

    return base64.b64encode(
        svg.encode("utf-8")
    ).decode("utf-8")


# =========================================================
# STYLES
# =========================================================

def inject_styles() -> None:
    topographic_background = (
        create_topographic_background()
    )

    css = """
    <style>
    :root {
        --background: #050910;
        --card-border: rgba(102, 207, 255, 0.18);
    }

    @keyframes titleEntrance {
        from {
            opacity: 0;
            transform: translateY(-18px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes cardEntrance {
        from {
            opacity: 0;
            transform: translateY(22px) scale(0.985);
        }

        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @keyframes winnerGlow {
        0%, 100% {
            box-shadow:
                0 16px 38px rgba(0, 0, 0, 0.34),
                0 0 12px rgba(255, 211, 56, 0.10);
        }

        50% {
            box-shadow:
                0 18px 44px rgba(0, 0, 0, 0.40),
                0 0 30px rgba(255, 211, 56, 0.22);
        }
    }

    @keyframes scoreEntrance {
        0% {
            opacity: 0;
            transform: scale(0.78);
        }

        70% {
            transform: scale(1.06);
        }

        100% {
            opacity: 1;
            transform: scale(1);
        }
    }

    .stApp {
        min-height: 100vh;

        background-color: var(--background);

        background-image:
            url("data:image/svg+xml;base64,__TOPOGRAPHIC_BACKGROUND__"),
            radial-gradient(
                circle at 8% 8%,
                rgba(0, 180, 255, 0.16),
                transparent 32%
            ),
            radial-gradient(
                circle at 92% 88%,
                rgba(29, 77, 255, 0.18),
                transparent 35%
            ),
            linear-gradient(
                145deg,
                #06101b 0%,
                #081422 42%,
                #060c15 72%,
                #03060b 100%
            );

        background-size:
            cover,
            auto,
            auto,
            auto;

        background-position:
            center center,
            left top,
            right bottom,
            center center;

        background-repeat:
            no-repeat,
            no-repeat,
            no-repeat,
            no-repeat;

        background-attachment:
            fixed,
            fixed,
            fixed,
            fixed;
    }

    [data-testid="stHeader"] {
        background: rgba(3, 7, 13, 0.38);
        backdrop-filter: blur(10px);
    }

    [data-testid="stToolbar"] {
        background: rgba(5, 11, 20, 0.60);
        border-radius: 10px;
    }

    .block-container {
        width: min(92vw, 1320px);
        max-width: 1320px;

        padding-top: 3.7rem !important;
        padding-right: 1.5rem;
        padding-bottom: 5rem;
        padding-left: 1.5rem;
    }

    .app-title {
        width: 100%;
        margin: 0 auto 0.45rem auto;

        color: #ffffff;
        text-align: center;

        font-size: clamp(2.3rem, 5vw, 3.65rem);
        font-weight: 900;
        line-height: 1.15;
        letter-spacing: 0.015em;

        text-shadow:
            0 0 22px rgba(65, 196, 255, 0.14);

        animation:
            titleEntrance 0.7s ease-out both;
    }

    .app-subtitle {
        margin-bottom: 2.2rem;

        color: rgba(202, 231, 248, 0.68);
        text-align: center;

        font-size: 1rem;
        letter-spacing: 0.025em;

        animation:
            titleEntrance 0.8s ease-out 0.08s both;
    }

    .section-title {
        display: flex;
        align-items: center;
        gap: 16px;

        margin-top: 2.2rem;
        margin-bottom: 1.25rem;

        color: #ffffff;

        font-size: 2rem;
        font-weight: 850;
    }

    .ranking-stars-image {
        display: block;

        width: 118px;
        height: 58px;

        object-fit: contain;

        filter:
            drop-shadow(
                0 5px 10px
                rgba(0, 0, 0, 0.32)
            );
    }

    .leaderboard-card {
        display: flex;
        align-items: center;
        gap: 24px;

        width: 100%;
        min-height: 155px;
        box-sizing: border-box;

        margin: 17px 0;
        padding: 28px 34px;

        background:
            linear-gradient(
                135deg,
                rgba(24, 40, 68, 0.94),
                rgba(10, 19, 34, 0.95)
            );

        border:
            1px solid
            var(--card-border);

        border-radius: 20px;

        backdrop-filter: blur(14px);

        box-shadow:
            0 16px 38px rgba(0, 0, 0, 0.34),
            inset 0 1px 0 rgba(255, 255, 255, 0.04);

        transition:
            transform 0.22s ease,
            border-color 0.22s ease,
            box-shadow 0.22s ease;

        animation:
            cardEntrance 0.58s
            ease-out
            var(--delay)
            both;
    }

    .leaderboard-card:hover {
        transform:
            translateY(-4px)
            scale(1.004);

        border-color:
            rgba(83, 208, 255, 0.42);

        box-shadow:
            0 21px 46px rgba(0, 0, 0, 0.42),
            0 0 24px rgba(36, 181, 255, 0.09),
            inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }

    .leaderboard-card.first-place {
        border-color:
            rgba(255, 211, 52, 0.72);

        animation:
            cardEntrance 0.58s
            ease-out
            var(--delay)
            both,
            winnerGlow 3s
            ease-in-out
            1.1s
            infinite;
    }

    .leaderboard-card.second-place {
        border-color:
            rgba(184, 220, 255, 0.48);
    }

    .leaderboard-card.third-place {
        border-color:
            rgba(225, 136, 65, 0.52);
    }

    .position {
        display: flex;
        align-items: center;
        justify-content: center;

        width: 104px;
        min-width: 104px;
        height: 104px;
    }

    .rank-icon-image {
        display: block;

        width: 96px;
        height: 96px;

        object-fit: contain;

        filter:
            drop-shadow(
                0 8px 18px
                rgba(0, 0, 0, 0.35)
            );
    }

    .leaderboard-card.third-place .rank-icon-image {
        transform: translateX(-5px);
    }

    .rank-fallback {
        display: flex;
        align-items: center;
        justify-content: center;

        width: 72px;
        height: 72px;

        border-radius: 50%;

        color: #ffffff;

        font-size: 2rem;
        font-weight: 900;

        background:
            linear-gradient(
                135deg,
                rgba(79, 200, 255, 0.18),
                rgba(255, 255, 255, 0.06)
            );

        border:
            1px solid
            rgba(130, 214, 255, 0.24);
    }

    .player-info {
        flex: 1;
        min-width: 0;
    }

    .player-name {
        color: #ffffff;

        font-size: 1.72rem;
        font-weight: 850;
        line-height: 1.2;

        overflow-wrap: anywhere;
    }

    .weekly-score {
        margin-top: 9px;

        color: rgba(197, 232, 253, 0.78);

        font-size: 0.96rem;
    }

    .movement {
        margin-top: 7px;

        color: rgba(183, 211, 231, 0.57);

        font-size: 0.86rem;
    }

    .total-score {
        min-width: 190px;

        color: #ffffff;
        text-align: right;

        font-size: 2.65rem;
        font-weight: 900;

        animation:
            scoreEntrance 0.7s
            ease-out
            calc(var(--delay) + 0.14s)
            both;
    }

    .total-score span {
        display: block;

        margin-top: 4px;

        color: rgba(188, 221, 242, 0.56);

        font-size: 0.68rem;
        font-weight: 650;
        text-transform: uppercase;
        letter-spacing: 0.09em;
    }

    [data-testid="stSidebar"] {
        background:
            radial-gradient(
                circle at top left,
                rgba(18, 153, 255, 0.10),
                transparent 35%
            ),
            linear-gradient(
                180deg,
                rgba(7, 14, 25, 0.98),
                rgba(4, 8, 15, 0.99)
            );

        border-right:
            1px solid
            rgba(72, 194, 255, 0.10);

        box-shadow:
            12px 0 40px
            rgba(0, 0, 0, 0.20);
    }

    [data-testid="stMetric"] {
        min-height: 130px;
        padding: 22px;

        background:
            linear-gradient(
                135deg,
                rgba(24, 40, 67, 0.91),
                rgba(11, 21, 38, 0.93)
            );

        border:
            1px solid
            rgba(95, 205, 255, 0.17);

        border-radius: 17px;

        backdrop-filter: blur(13px);

        box-shadow:
            0 13px 32px
            rgba(0, 0, 0, 0.28);

        transition:
            transform 0.2s ease,
            border-color 0.2s ease,
            box-shadow 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);

        border-color:
            rgba(95, 205, 255, 0.35);

        box-shadow:
            0 17px 38px rgba(0, 0, 0, 0.34),
            0 0 22px rgba(38, 183, 255, 0.08);
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {
        color: #ffffff;
    }

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 12px;
        font-weight: 700;

        transition:
            transform 0.2s ease,
            border-color 0.2s ease,
            box-shadow 0.2s ease;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-2px);

        border-color:
            rgba(78, 201, 255, 0.55);

        box-shadow:
            0 8px 22px
            rgba(0, 153, 255, 0.13);
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color:
            rgba(8, 17, 30, 0.94);

        border-color:
            rgba(87, 203, 255, 0.16);
    }

    [data-testid="stDataFrame"] {
        border:
            1px solid
            rgba(87, 203, 255, 0.13);

        border-radius: 14px;
        overflow: hidden;
    }

    @media (max-width: 900px) {
        .block-container {
            width: 100%;
            padding-top: 4rem !important;
        }

        .leaderboard-card {
            gap: 15px;
            min-height: 130px;
            padding: 21px 19px;
        }

        .position {
            width: 80px;
            min-width: 80px;
            height: 80px;
        }

        .rank-icon-image {
            width: 72px;
            height: 72px;
        }

        .player-name {
            font-size: 1.3rem;
        }

        .total-score {
            min-width: 115px;
            font-size: 1.9rem;
        }
    }

    @media (max-width: 650px) {
        .app-title {
            font-size: 1.85rem;
        }

        .ranking-stars-image {
            width: 86px;
            height: 45px;
        }

        .section-title {
            gap: 10px;
            font-size: 1.6rem;
        }

        .leaderboard-card {
            gap: 10px;
            min-height: 115px;
            padding: 17px 13px;
        }

        .position {
            width: 58px;
            min-width: 58px;
            height: 58px;
        }

        .rank-icon-image {
            width: 54px;
            height: 54px;
        }

        .rank-fallback {
            width: 44px;
            height: 44px;
            font-size: 1.1rem;
        }

        .player-name {
            font-size: 1.05rem;
        }

        .weekly-score {
            font-size: 0.7rem;
        }

        .movement {
            font-size: 0.65rem;
        }

        .total-score {
            min-width: 75px;
            font-size: 1.4rem;
        }

        .total-score span {
            font-size: 0.43rem;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration:
                0.01ms !important;

            animation-iteration-count:
                1 !important;

            scroll-behavior:
                auto !important;
        }
    }
    </style>
    """

    css = css.replace(
        "__TOPOGRAPHIC_BACKGROUND__",
        topographic_background,
    )

    st.markdown(
        css,
        unsafe_allow_html=True,
    )


# =========================================================
# LEADERBOARD
# =========================================================

def show_leaderboard(
    data: dict,
) -> None:
    if not data["players"]:
        st.info(
            "There are no participants yet. "
            "Add participants from the menu."
        )
        return

    ranking = sorted(
        data["players"],
        key=lambda player: (
            -int(player["total"]),
            player["id"],
        ),
    )

    previous_ranking = (
        get_previous_ranking(data)
    )

    total_team_tickets = sum(
        int(player["total"])
        for player in data["players"]
    )

    latest_week_total = sum(
        get_latest_week_score(
            data,
            player["id"],
        )
        for player in data["players"]
    )

    metric_1, metric_2, metric_3 = st.columns(3)

    with metric_1:
        st.metric(
            "Participants",
            len(data["players"]),
        )

    with metric_2:
        st.metric(
            "Global Tickets",
            f"{total_team_tickets:,}",
        )

    with metric_3:
        st.metric(
            "Latest Week",
            f"{latest_week_total:,}",
        )

    ranking_stars_html = (
        get_ranking_stars_html()
    )

    render_html(
        f"""
        <div class="section-title">
            {ranking_stars_html}
            <span>RANKING</span>
        </div>
        """
    )

    card_classes = {
        1: "first-place",
        2: "second-place",
        3: "third-place",
    }

    for position, player in enumerate(
        ranking,
        start=1,
    ):
        rank_icon_html = (
            get_rank_icon_html(position)
        )

        weekly_score = (
            get_latest_week_score(
                data,
                player["id"],
            )
        )

        previous_position = (
            previous_ranking.get(
                player["id"],
            )
        )

        if previous_position is None:
            movement_text = (
                "No previous comparison"
            )

        elif previous_position > position:
            difference = (
                previous_position
                - position
            )

            label = (
                "position"
                if difference == 1
                else "positions"
            )

            movement_text = (
                f"▲ Moved up "
                f"{difference} {label}"
            )

        elif previous_position < position:
            difference = (
                position
                - previous_position
            )

            label = (
                "position"
                if difference == 1
                else "positions"
            )

            movement_text = (
                f"▼ Moved down "
                f"{difference} {label}"
            )

        else:
            movement_text = "— No change"

        card_class = card_classes.get(
            position,
            "",
        )

        safe_name = html.escape(
            str(player["name"])
        )

        safe_movement = html.escape(
            movement_text
        )

        animation_delay = (
            position * 0.08
        )

        render_html(
            f"""
            <div
                class="leaderboard-card {card_class}"
                style="--delay: {animation_delay:.2f}s;"
            >
                <div class="position">
                    {rank_icon_html}
                </div>

                <div class="player-info">
                    <div class="player-name">
                        {safe_name}
                    </div>

                    <div class="weekly-score">
                        +{weekly_score:,} tickets in the latest week
                    </div>

                    <div class="movement">
                        {safe_movement}
                    </div>
                </div>

                <div class="total-score">
                    {int(player["total"]):,}
                    <span>Global tickets</span>
                </div>
            </div>
            """
        )


# =========================================================
# ADD WEEKLY RESULTS
# =========================================================

def add_weekly_tickets_page(
    data: dict,
) -> None:
    st.header(
        "➕ Add This Week's Tickets"
    )

    if not data["players"]:
        st.warning(
            "Add at least one participant first."
        )
        return

    selected_date = st.date_input(
        "Week date",
        value=date.today(),
    )

    st.caption(
        "The values entered here will be added "
        "to each participant's global total."
    )

    weekly_inputs = {}

    with st.form("weekly_form"):
        columns = st.columns(2)

        for index, player in enumerate(
            data["players"]
        ):
            with columns[index % 2]:
                weekly_inputs[player["id"]] = (
                    st.number_input(
                        player["name"],
                        min_value=0,
                        step=1,
                        value=0,
                        key=f"weekly_{player['id']}",
                    )
                )

        submitted = st.form_submit_button(
            "Save Weekly Results",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    total_entered = sum(
        int(value)
        for value in weekly_inputs.values()
    )

    if total_entered == 0:
        st.warning(
            "All values are currently zero."
        )
        return

    date_string = selected_date.isoformat()

    existing_week = next(
        (
            entry
            for entry in data["history"]
            if entry.get("date") == date_string
        ),
        None,
    )

    if existing_week is not None:
        st.error(
            "An entry already exists for this date."
        )
        return

    entry = {
        "date": date_string,
        "created_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "scores": [],
    }

    for player_id, tickets in weekly_inputs.items():
        player = get_player(
            data,
            player_id,
        )

        if player is None:
            continue

        ticket_value = int(tickets)

        player["total"] = (
            int(player["total"])
            + ticket_value
        )

        entry["scores"].append(
            {
                "player_id": player_id,
                "player_name": player["name"],
                "tickets": ticket_value,
            }
        )

    data["history"].append(entry)

    data["history"].sort(
        key=lambda item: item.get(
            "date",
            "",
        )
    )

    save_data(data)

    st.success(
        f"{total_entered:,} tickets were added."
    )

    st.rerun()


# =========================================================
# MANAGE PARTICIPANTS
# =========================================================

def manage_players_page(
    data: dict,
) -> None:
    st.header(
        "👥 Manage Participants"
    )

    st.write(
        f"Current participants: "
        f"**{len(data['players'])}/{MAX_PLAYERS}**"
    )

    for player in list(data["players"]):
        name_column, save_column, delete_column = (
            st.columns([4, 1.4, 1.4])
        )

        with name_column:
            new_name = st.text_input(
                "Name",
                value=player["name"],
                key=f"name_{player['id']}",
                label_visibility="collapsed",
            )

        with save_column:
            save_clicked = st.button(
                "Save",
                key=f"save_{player['id']}",
                use_container_width=True,
            )

        with delete_column:
            delete_clicked = st.button(
                "Delete",
                key=f"delete_{player['id']}",
                use_container_width=True,
            )

        if save_clicked:
            cleaned_name = new_name.strip()

            if not cleaned_name:
                st.error(
                    "The name cannot be empty."
                )
                return

            duplicate = any(
                other["id"] != player["id"]
                and other["name"].strip().lower()
                == cleaned_name.lower()
                for other in data["players"]
            )

            if duplicate:
                st.error(
                    "Another participant already "
                    "uses this name."
                )
                return

            player["name"] = cleaned_name

            for entry in data["history"]:
                for score in entry.get("scores", []):
                    if (
                        int(score.get("player_id", -1))
                        == player["id"]
                    ):
                        score["player_name"] = (
                            cleaned_name
                        )

            save_data(data)
            st.rerun()

        if delete_clicked:
            data["players"] = [
                item
                for item in data["players"]
                if item["id"] != player["id"]
            ]

            save_data(data)
            st.rerun()

    st.divider()

    if len(data["players"]) >= MAX_PLAYERS:
        st.info(
            "The maximum of 8 participants "
            "has been reached."
        )
        return

    with st.form(
        "add_player_form",
        clear_on_submit=True,
    ):
        new_player_name = st.text_input(
            "New participant name"
        )

        add_player = st.form_submit_button(
            "Add Participant",
            type="primary",
            use_container_width=True,
        )

    if not add_player:
        return

    cleaned_name = new_player_name.strip()

    if not cleaned_name:
        st.error(
            "Enter a participant name."
        )
        return

    existing_names = {
        player["name"].strip().lower()
        for player in data["players"]
    }

    if cleaned_name.lower() in existing_names:
        st.error(
            "A participant with this name "
            "already exists."
        )
        return

    data["players"].append(
        {
            "id": data["next_player_id"],
            "name": cleaned_name,
            "total": 0,
        }
    )

    data["next_player_id"] += 1

    save_data(data)
    st.rerun()


# =========================================================
# EDIT GLOBAL TICKETS
# =========================================================

def edit_global_tickets_page(
    data: dict,
) -> None:
    st.header(
        "🎟️ Edit Global Tickets"
    )

    if not data["players"]:
        st.info(
            "There are no participants."
        )
        return

    st.warning(
        "These values directly change the global totals. "
        "The weekly history will remain unchanged."
    )

    new_totals = {}

    with st.form("global_tickets_form"):
        columns = st.columns(2)

        for index, player in enumerate(
            data["players"]
        ):
            with columns[index % 2]:
                new_totals[player["id"]] = (
                    st.number_input(
                        player["name"],
                        min_value=0,
                        step=1,
                        value=int(player["total"]),
                        key=f"global_{player['id']}",
                    )
                )

        submitted = st.form_submit_button(
            "Save Global Tickets",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    for player_id, new_total in new_totals.items():
        player = get_player(
            data,
            player_id,
        )

        if player is not None:
            player["total"] = int(new_total)

    save_data(data)

    st.success(
        "Global ticket totals were updated."
    )

    st.rerun()


# =========================================================
# HISTORY
# =========================================================

def history_page(
    data: dict,
) -> None:
    st.header(
        "📅 Weekly History"
    )

    if not data["history"]:
        st.info(
            "No weekly results have been recorded yet."
        )
        return

    rows = []

    for entry in reversed(data["history"]):
        for score in entry.get("scores", []):
            rows.append(
                {
                    "Week": entry.get(
                        "date",
                        "",
                    ),
                    "Participant": score.get(
                        "player_name",
                        "Unknown",
                    ),
                    "Tickets": int(
                        score.get(
                            "tickets",
                            0,
                        )
                    ),
                }
            )

    dataframe = pd.DataFrame(rows)

    st.dataframe(
        dataframe,
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

    st.subheader(
        "Delete Latest Week"
    )

    latest_entry = data["history"][-1]

    st.warning(
        "This will subtract the tickets recorded "
        f"on {latest_entry['date']}."
    )

    confirmation = st.checkbox(
        "I confirm that I want to "
        "delete the latest week."
    )

    if st.button(
        "Delete Latest Week",
        disabled=not confirmation,
        use_container_width=True,
    ):
        removed_entry = data["history"].pop()

        for score in removed_entry.get("scores", []):
            player = get_player(
                data,
                int(score["player_id"]),
            )

            if player is not None:
                player["total"] = max(
                    0,
                    int(player["total"])
                    - int(score["tickets"]),
                )

        save_data(data)
        st.rerun()


# =========================================================
# CHARTS
# =========================================================

def charts_page(
    data: dict,
) -> None:
    st.header("📊 Charts")

    if not data["players"]:
        st.info(
            "There are no participants."
        )
        return

    ranking = sorted(
        data["players"],
        key=lambda player: (
            -int(player["total"]),
            player["id"],
        ),
    )

    chart_data = pd.DataFrame(
        {
            "Name": [
                player["name"]
                for player in ranking
            ],
            "Tickets": [
                int(player["total"])
                for player in ranking
            ],
        }
    )

    st.subheader(
        "Global Tickets"
    )

    st.bar_chart(
        chart_data,
        x="Name",
        y="Tickets",
        use_container_width=True,
    )

    if not data["history"]:
        st.info(
            "Add at least one week "
            "to view progress."
        )
        return

    weekly_rows = []

    for entry in data["history"]:
        week_total = sum(
            int(score.get("tickets", 0))
            for score in entry.get("scores", [])
        )

        weekly_rows.append(
            {
                "Week": entry["date"],
                "Tickets": week_total,
            }
        )

    weekly_dataframe = pd.DataFrame(
        weekly_rows
    )

    st.subheader(
        "Tickets Produced per Week"
    )

    st.line_chart(
        weekly_dataframe,
        x="Week",
        y="Tickets",
        use_container_width=True,
    )

    player_weekly_rows = []

    for entry in data["history"]:
        row = {
            "Week": entry["date"],
        }

        for player in data["players"]:
            row[player["name"]] = 0

        for score in entry.get("scores", []):
            player = get_player(
                data,
                int(score["player_id"]),
            )

            if player is not None:
                row[player["name"]] = int(
                    score.get(
                        "tickets",
                        0,
                    )
                )

        player_weekly_rows.append(row)

    player_weekly_dataframe = pd.DataFrame(
        player_weekly_rows
    )

    st.subheader(
        "Results by Participant"
    )

    st.line_chart(
        player_weekly_dataframe,
        x="Week",
        use_container_width=True,
    )


# =========================================================
# RESET
# =========================================================

def reset_page(
    data: dict,
) -> None:
    st.header(
        "🧨 Reset Leaderboard"
    )

    st.warning(
        "This will set every global ticket total to zero "
        "and permanently delete the weekly history."
    )

    confirmation = st.text_input(
        'Type "RESET" to confirm'
    )

    if st.button(
        "Reset All Scores",
        type="primary",
        use_container_width=True,
    ):
        if confirmation != "RESET":
            st.error(
                'You must type exactly "RESET".'
            )
            return

        for player in data["players"]:
            player["total"] = 0

        data["history"] = []

        save_data(data)

        st.success(
            "The leaderboard was reset."
        )

        st.rerun()


# =========================================================
# MAIN APPLICATION
# =========================================================

def main() -> None:
    st.set_page_config(
        page_title="TYS Techs Leaderboard",
        page_icon="⭐",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_styles()

    data = load_data()

    render_html(
        """
        <div class="app-title">
            TYS TECHS LEADERBOARD
        </div>

        <div class="app-subtitle">
            Weekly ticket tracking
        </div>
        """
    )

    menu = st.sidebar.radio(
        "Menu",
        [
            "Leaderboard",
            "Add This Week",
            "Manage Participants",
            "Edit Global Tickets",
            "History",
            "Charts",
            "Reset Leaderboard",
        ],
    )

    if menu == "Leaderboard":
        show_leaderboard(data)

    elif menu == "Add This Week":
        add_weekly_tickets_page(data)

    elif menu == "Manage Participants":
        manage_players_page(data)

    elif menu == "Edit Global Tickets":
        edit_global_tickets_page(data)

    elif menu == "History":
        history_page(data)

    elif menu == "Charts":
        charts_page(data)

    elif menu == "Reset Leaderboard":
        reset_page(data)


if __name__ == "__main__":
    main()