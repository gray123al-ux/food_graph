
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# =========================================================
# PAGE
# =========================================================
st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide"
)

# =========================================================
# DARK MODE CSS
# =========================================================
st.markdown("""
<style>

/* 전체 배경 */
.stApp {
    background-color: #0e1117;
    color: #f1f5f9;
}

/* 메인 영역 */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* 제목 */
.main-title {
    font-size: 44px;
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 5px;
}

.subtitle {
    color: #94a3b8;
    font-size: 17px;
    margin-bottom: 30px;
}

/* 섹션 제목 */
.section-title {
    font-size: 27px;
    font-weight: 750;
    color: #f8fafc;
    margin-top: 35px;
    margin-bottom: 15px;
}

/* Metric */
div[data-testid="stMetric"] {
    background: #151a23;
    border: 1px solid #293241;
    border-radius: 16px;
    padding: 20px;
}

div[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}

div[data-testid="stMetricValue"] {
    color: #f8fafc !important;
}

/* 사용자 정의 카드 */
.metric-card {
    background: #151a23;
    border: 1px solid #293241;
    border-radius: 18px;
    padding: 25px;
    text-align: center;
}

.metric-title {
    color: #94a3b8;
    font-size: 15px;
}

.metric-value {
    color: #f8fafc;
    font-size: 36px;
    font-weight: 800;
    margin-top: 8px;
}

/* 예측 박스 */
.prediction-box {
    background: #151a23;
    border: 1px solid #334155;
    border-radius: 22px;
    padding: 40px;
    text-align: center;
    margin: 25px 0;
}

.prediction-year {
    color: #94a3b8;
    font-size: 22px;
}

.prediction-value {
    color: #f8fafc;
    font-size: 60px;
    font-weight: 900;
    margin: 10px 0;
}

.prediction-description {
    color: #64748b;
}

/* Info / warning / success */
div[data-testid="stAlert"] {
    background-color: #151a23;
    color: #cbd5e1;
    border-radius: 14px;
}

/* Expander */
div[data-testid="stExpander"] {
    background-color: #151a23;
    border: 1px solid #293241;
    border-radius: 14px;
}

div[data-testid="stExpander"] p,
div[data-testid="stExpander"] li {
    color: #cbd5e1;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border: 1px solid #293241;
    border-radius: 12px;
}

/* Slider */
div[data-testid="stSlider"] label {
    color: #cbd5e1 !important;
}

/* Markdown */
p, li {
    color: #cbd5e1;
}

/* Caption */
.stCaption {
    color: #64748b !important;
}

/* Horizontal line */
hr {
    border-color: #293241;
}

/* Selectbox / inputs */
div[data-baseweb="select"] > div {
    background-color: #151a23;
    border-color: #334155;
    color: #f8fafc;
}

/* Button */
.stButton > button {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 10px;
}

.stButton > button:hover {
    background-color: #334155;
    border-color: #475569;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# PLOTLY DARK THEME
# =========================================================
PLOT_BG = "#0e1117"
PAPER_BG = "#0e1117"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "#293241"


def dark_layout(fig, height=550):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(
            color=TEXT_COLOR
        ),
        height=height,
        hovermode="x unified",
        xaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)"
        )
    )

    return fig


# =========================================================
# TITLE
# =========================================================
st.markdown(
    '<div class="main-title">🌡️ 기온 예측기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '서울의 장기 기온 데이터를 이용해 기온 변화 추세와 미래의 예상 기온을 살펴봅니다.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# DATA
# =========================================================
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)


@st.cache_data
def load_data():

    df = pd.read_csv(
        DATA_URL,
        encoding="utf-8"
    )

    df["날짜"] = pd.to_datetime(
        df["날짜"],
        errors="coerce"
    )

    for col in [
        "평균기온",
        "최저기온",
        "최고기온"
    ]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df["연도"] = df["날짜"].dt.year

    return df


try:
    df = load_data()

except Exception as e:

    st.error(
        "기온 데이터를 불러오지 못했습니다."
    )

    st.exception(e)

    st.stop()


# =========================================================
# ANALYSIS PERIOD
# =========================================================
df = df[
    df["연도"] <= 2025
].copy()

valid_temp = df.dropna(
    subset=["평균기온"]
)

year_count = (
    valid_temp
    .groupby("연도")
    .size()
)

valid_years = year_count[
    year_count >= 300
].index

df_valid = valid_temp[
    valid_temp["연도"].isin(valid_years)
].copy()


# =========================================================
# ANNUAL DATA
# =========================================================
annual = (
    df_valid
    .groupby("연도")
    .agg(
        연평균기온=("평균기온", "mean"),
        연최저기온=("최저기온", "min"),
        연최고기온=("최고기온", "max"),
        관측일수=("평균기온", "count")
    )
    .reset_index()
    .sort_values("연도")
)

if len(annual) < 2:

    st.error(
        "분석할 수 있는 연도가 충분하지 않습니다."
    )

    st.stop()


# =========================================================
# REGRESSION
# =========================================================
BASE_YEAR = 1908

annual["경과연수"] = (
    annual["연도"] - BASE_YEAR
)

x = annual["경과연수"].to_numpy()
y = annual["연평균기온"].to_numpy()

slope, intercept = np.polyfit(
    x,
    y,
    1
)

annual["전체회귀기온"] = (
    slope * x + intercept
)

correlation = np.corrcoef(
    x,
    y
)[0, 1]

slope_100 = slope * 100


# =========================================================
# RECENT 20 YEARS
# =========================================================
last_year = int(
    annual["연도"].max()
)

recent_start = last_year - 19

recent = annual[
    annual["연도"] >= recent_start
].copy()

if len(recent) >= 2:

    rx = (
        recent["연도"] - BASE_YEAR
    ).to_numpy()

    ry = recent["연평균기온"].to_numpy()

    recent_slope, recent_intercept = np.polyfit(
        rx,
        ry,
        1
    )

    recent_slope_100 = (
        recent_slope * 100
    )

    recent["최근20년회귀"] = (
        recent_slope * rx +
        recent_intercept
    )

else:

    recent_slope_100 = np.nan


# =========================================================
# ABNORMAL YEARS
# =========================================================
mean_temp = (
    annual["연평균기온"].mean()
)

std_temp = (
    annual["연평균기온"].std()
)

annual["이상기온"] = np.where(
    annual["연평균기온"]
    > mean_temp + std_temp,
    "높음",
    np.where(
        annual["연평균기온"]
        < mean_temp - std_temp,
        "낮음",
        ""
    )
)


# =========================================================
# KEY RESULTS
# =========================================================
st.markdown(
    '<div class="section-title">📌 핵심 결과</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "분석 기간",
        f"{annual['연도'].min()}~{annual['연도'].max()}"
    )

with c2:
    st.metric(
        "평균 기온",
        f"{mean_temp:.2f} °C"
    )

with c3:
    st.metric(
        "상관계수",
        f"{correlation:.3f}"
    )

with c4:
    st.metric(
        "100년당 변화",
        f"{slope_100:+.2f} °C"
    )


# =========================================================
# COMPARISON
# =========================================================
st.markdown(
    '<div class="section-title">📈 기온 변화 속도 비교</div>',
    unsafe_allow_html=True
)

c1, c2 = st.columns(2)

with c1:

    st.markdown(
        '<div class="metric-card">'
        '<div class="metric-title">'
        '전체 기간'
        '</div>'
        f'<div class="metric-value">'
        f'{slope_100:+.2f} °C'
        '</div>'
        '<div class="metric-title">'
        '100년당 변화량'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

with c2:

    if not np.isnan(recent_slope_100):

        st.markdown(
            '<div class="metric-card">'
            '<div class="metric-title">'
            '최근 20년'
            '</div>'
            f'<div class="metric-value">'
            f'{recent_slope_100:+.2f} °C'
            '</div>'
            '<div class="metric-title">'
            '100년당 변화량'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )


# =========================================================
# MAIN GRAPH
# =========================================================
st.markdown(
    '<div class="section-title">'
    '📊 서울 연평균 기온 변화'
    '</div>',
    unsafe_allow_html=True
)

fig = go.Figure()


# Actual
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연평균기온"],
        mode="markers",
        name="연평균 기온",
        marker=dict(
            size=7
        ),
        customdata=annual[
            ["관측일수", "이상기온"]
        ],
        hovertemplate=
        "<b>%{x}년</b><br>"
        "연평균 기온: %{y:.2f} °C<br>"
        "관측일수: %{customdata[0]}일<br>"
        "이상기온: %{customdata[1]}"
        "<extra></extra>"
    )
)


# Full regression
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["전체회귀기온"],
        mode="lines",
        name="전체 기간 회귀선",
        line=dict(
            width=3
        )
    )
)


# Recent regression
if len(recent) >= 2:

    fig.add_trace(
        go.Scatter(
            x=recent["연도"],
            y=recent["최근20년회귀"],
            mode="lines",
            name="최근 20년 회귀선",
            line=dict(
                width=3,
                dash="dash"
            )
        )
    )


dark_layout(
    fig,
    600
)

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균 기온 (°C)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.info(
    "실제 연평균 기온과 두 개의 회귀선을 비교하면 "
    "장기적인 변화와 최근 변화의 차이를 확인할 수 있습니다."
)


# =========================================================
# WARMEST / COLDEST
# =========================================================
st.markdown(
    '<div class="section-title">'
    '🔥 가장 따뜻한 해와 가장 추운 해'
    '</div>',
    unsafe_allow_html=True
)

warmest = annual.loc[
    annual["연평균기온"].idxmax()
]

coldest = annual.loc[
    annual["연평균기온"].idxmin()
]

c1, c2 = st.columns(2)

with c1:

    st.metric(
        "🔥 가장 따뜻한 해",
        f"{int(warmest['연도'])}년"
    )

    st.write(
        f"연평균 기온: "
        f"**{warmest['연평균기온']:.2f} °C**"
    )

with c2:

    st.metric(
        "❄️ 가장 추운 해",
        f"{int(coldest['연도'])}년"
    )

    st.write(
        f"연평균 기온: "
        f"**{coldest['연평균기온']:.2f} °C**"
    )


# =========================================================
# TEMPERATURE RANGE
# =========================================================
st.markdown(
    '<div class="section-title">'
    '🌡️ 연도별 기온 범위'
    '</div>',
    unsafe_allow_html=True
)

fig2 = go.Figure()

fig2.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연최고기온"],
        mode="lines",
        name="연중 최고기온",
        line=dict(
            width=2
        )
    )
)

fig2.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연평균기온"],
        mode="lines",
        name="연평균기온",
        line=dict(
            width=3
        )
    )
)

fig2.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연최저기온"],
        mode="lines",
        name="연중 최저기온",
        line=dict(
            width=2
        )
    )
)

dark_layout(
    fig2,
    500
)

fig2.update_layout(
    xaxis_title="연도",
    yaxis_title="기온 (°C)"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# =========================================================
# PREDICTION
# =========================================================
st.markdown(
    '<div class="section-title">'
    '🔮 미래 기온 예측'
    '</div>',
    unsafe_allow_html=True
)

future_max = last_year + 50

selected_year = st.slider(
    "예측할 연도",
    min_value=int(
        annual["연도"].min()
    ),
    max_value=future_max,
    value=last_year,
    step=1
)

selected_x = (
    selected_year - BASE_YEAR
)

predicted_temp = (
    slope * selected_x +
    intercept
)

st.markdown(
    f"""
    <div class="prediction-box">

        <div class="prediction-year">
            {selected_year}년 예상 연평균 기온
        </div>

        <div class="prediction-value">
            {predicted_temp:.2f} °C
        </div>

        <div class="prediction-description">
            과거 전체 기간의 선형 회귀 추세를 연장한 통계적 추정값
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# FUTURE GRAPH
# =========================================================
prediction_years = np.arange(
    int(annual["연도"].min()),
    future_max + 1
)

prediction_x = (
    prediction_years - BASE_YEAR
)

prediction_temp = (
    slope * prediction_x +
    intercept
)

fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연평균기온"],
        mode="markers",
        name="실제 기온"
    )
)

fig3.add_trace(
    go.Scatter(
        x=prediction_years,
        y=prediction_temp,
        mode="lines",
        name="회귀 기반 예측",
        line=dict(
            dash="dash",
            width=3
        )
    )
)

fig3.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temp],
        mode="markers",
        name="선택한 연도",
        marker=dict(
            size=16
        )
    )
)

dark_layout(
    fig3,
    520
)

fig3.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균 기온 (°C)"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)


# =========================================================
# ABNORMAL YEARS
# =========================================================
st.markdown(
    '<div class="section-title">'
    '⚠️ 눈에 띄는 연도'
    '</div>',
    unsafe_allow_html=True
)

abnormal = annual[
    annual["이상기온"] != ""
].copy()

if len(abnormal) > 0:

    fig4 = px.bar(
        abnormal,
        x="연도",
        y="연평균기온",
        color="이상기온",
        hover_data=[
            "관측일수"
        ],
        labels={
            "연도": "연도",
            "연평균기온": "연평균 기온 (°C)",
            "이상기온": "구분"
        }
    )

    dark_layout(
        fig4,
        450
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )

    st.caption(
        "평균에서 표준편차만큼 벗어난 연도를 표시했습니다."
    )

else:

    st.info(
        "통계적으로 크게 벗어난 연도가 없습니다."
    )


# =========================================================
# DATA QUALITY
# =========================================================
st.markdown(
    '<div class="section-title">'
    '🔎 데이터 품질 확인'
    '</div>',
    unsafe_allow_html=True
)

all_years = set(
    range(
        int(df["연도"].min()),
        2026
    )
)

used_years = set(
    annual["연도"]
)

excluded_years = sorted(
    all_years - used_years
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "전체 연도",
        f"{len(all_years)}년"
    )

with c2:
    st.metric(
        "분석에 사용",
        f"{len(used_years)}년"
    )

with c3:
    st.metric(
        "제외된 연도",
        f"{len(excluded_years)}년"
    )

if excluded_years:

    st.write(
        "300일 미만 관측으로 제외된 연도:",
        ", ".join(
            map(
                str,
                excluded_years
            )
        )
    )


# =========================================================
# TABLE
# =========================================================
st.markdown(
    '<div class="section-title">'
    '📋 연도별 데이터'
    '</div>',
    unsafe_allow_html=True
)

display_df = annual[
    [
        "연도",
        "연평균기온",
        "연최저기온",
        "연최고기온",
        "관측일수"
    ]
].copy()

display_df[
    "연평균기온"
] = display_df[
    "연평균기온"
].round(2)

display_df[
    "연최저기온"
] = display_df[
    "연최저기온"
].round(1)

display_df[
    "연최고기온"
] = display_df[
    "연최고기온"
].round(1)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# METHOD
# =========================================================
with st.expander("ℹ️ 이 앱은 어떻게 계산하나요?"):

    st.markdown("""
### ① 연평균 기온

서울의 일별 `평균기온`을 연도별로 평균내어 계산합니다.

### ② 데이터가 부족한 연도

평균기온 관측일수가 **300일 미만인 연도는 제외**합니다.

### ③ 분석 기간

**2025년까지**의 데이터만 사용합니다.

### ④ 전체 기간 회귀

연도를 `연도 - 1908`로 바꾸어 선형 회귀를 계산합니다.

### ⑤ 100년당 변화량

회귀선의 기울기에 100을 곱합니다.

예를 들어 기울기가 `0.015`라면

`0.015 × 100 = 1.5`

이므로 **100년에 1.5°C 변화하는 추세**라는 뜻입니다.

### ⑥ 최근 20년

가장 최근 20개의 분석 연도만 따로 사용해 같은 방법으로 회귀분석합니다.

### ⑦ 미래 예측

과거의 선형 추세가 미래에도 그대로 이어진다고 가정하여 계산한 통계적 추정값입니다.

실제 미래 기온을 보장하는 예측은 아닙니다.
""")
