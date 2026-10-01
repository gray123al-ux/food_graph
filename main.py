import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide"
)


# =========================================================
# DARK MODE STYLE
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
        color: #f1f5f9;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 22px;
        text-align: center;
        margin-bottom: 10px;
    }

    .metric-title {
        color: #94a3b8;
        font-size: 15px;
        margin-bottom: 8px;
    }

    .metric-value {
        color: #f8fafc;
        font-size: 30px;
        font-weight: 800;
    }

    .prediction-box {
        background: #172033;
        border: 1px solid #3b82f6;
        border-radius: 18px;
        padding: 30px;
        text-align: center;
        margin: 20px 0 30px 0;
    }

    .prediction-year {
        color: #93c5fd;
        font-size: 20px;
    }

    .prediction-value {
        color: #ffffff;
        font-size: 48px;
        font-weight: 800;
        margin-top: 8px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 30px;
        margin-bottom: 12px;
    }

    .info-box {
        background: #161b22;
        border-left: 4px solid #3b82f6;
        padding: 15px 18px;
        border-radius: 8px;
        margin: 15px 0;
        color: #cbd5e1;
    }

    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 15px;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #30363d;
        border-radius: 10px;
    }

    div[data-baseweb="select"] > div {
        background-color: #161b22;
    }

    div[data-baseweb="input"] > div {
        background-color: #161b22;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# TITLE
# =========================================================
st.markdown(
    '<div class="main-title">🌡️ 기온 예측기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '서울의 장기 기온 데이터를 이용해 연평균 기온의 변화 추세를 살펴봅니다.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# DATA URL
# =========================================================
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)

BASE_YEAR = 1908


# =========================================================
# DATA LOADING
# =========================================================
@st.cache_data
def load_data():

    df = pd.read_csv(
        DATA_URL,
        encoding="utf-8"
    )

    # -----------------------------------------------------
    # 날짜 형식 정리
    # -----------------------------------------------------
    df["날짜"] = (
        df["날짜"]
        .astype(str)
        .str.strip()
        .str.replace("/", "-", regex=False)
        .str.replace(".", "-", regex=False)
    )

    # YYYY-MM-DD 형식으로 명시적으로 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"],
        format="%Y-%m-%d",
        errors="coerce"
    )

    # -----------------------------------------------------
    # 기온 데이터 숫자 변환
    # -----------------------------------------------------
    for col in [
        "평균기온",
        "최저기온",
        "최고기온"
    ]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # -----------------------------------------------------
    # 연도 생성
    # -----------------------------------------------------
    df["연도"] = df["날짜"].dt.year

    return df


# =========================================================
# LOAD DATA
# =========================================================
try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
    st.stop()


# =========================================================
# BASIC DATA CLEANING
# =========================================================

# 2025년까지만 사용
df = df[
    (df["연도"].notna()) &
    (df["연도"] <= 2025)
].copy()


# =========================================================
# ANNUAL DATA
# =========================================================

annual = (
    df.dropna(subset=["평균기온"])
    .groupby("연도")
    .agg(
        평균기온=("평균기온", "mean"),
        관측일수=("평균기온", "count"),
        최저기온=("평균기온", "min"),
        최고기온=("평균기온", "max")
    )
    .reset_index()
)

# 관측일수가 300일 이상인 연도만 사용
annual = annual[
    annual["관측일수"] >= 300
].copy()

annual["연도"] = annual["연도"].astype(int)

annual = annual.sort_values("연도").reset_index(drop=True)


# =========================================================
# CHECK DATA
# =========================================================
if len(annual) < 2:
    st.error("회귀분석을 할 수 있는 연도 데이터가 충분하지 않습니다.")
    st.stop()


# =========================================================
# REGRESSION FUNCTION
# =========================================================
def calculate_regression(data):

    x = data["연도"].values - BASE_YEAR
    y = data["평균기온"].values

    slope, intercept = np.polyfit(x, y, 1)

    predicted = slope * x + intercept

    correlation = np.corrcoef(x, y)[0, 1]

    return slope, intercept, correlation, predicted


# =========================================================
# FULL PERIOD REGRESSION
# =========================================================
full_slope, full_intercept, full_corr, annual["전체추세"] = (
    calculate_regression(annual)
)

full_slope_100 = full_slope * 100


# =========================================================
# RECENT 20 YEARS REGRESSION
# =========================================================
last_year = int(annual["연도"].max())

recent_start = last_year - 19

recent20 = annual[
    annual["연도"] >= recent_start
].copy()

if len(recent20) >= 2:

    recent_slope, recent_intercept, recent_corr, recent20["최근20년추세"] = (
        calculate_regression(recent20)
    )

    recent_slope_100 = recent_slope * 100

else:

    recent_slope = np.nan
    recent_intercept = np.nan
    recent_corr = np.nan
    recent_slope_100 = np.nan


# =========================================================
# HEADER METRICS
# =========================================================
st.markdown(
    '<div class="section-title">📊 핵심 결과</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "분석 기간",
        f"{annual['연도'].min()}–{annual['연도'].max()}"
    )

with col2:
    st.metric(
        "사용한 연도",
        f"{len(annual):,}년"
    )

with col3:
    st.metric(
        "전체 기간 상관계수",
        f"{full_corr:.3f}"
    )

with col4:
    st.metric(
        "최근 20년 상관계수",
        f"{recent_corr:.3f}"
        if not np.isnan(recent_corr)
        else "-"
    )


# =========================================================
# SLOPE COMPARISON
# =========================================================
st.markdown(
    '<div class="section-title">📈 100년에 몇 도 오르는가?</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">전체 기간</div>
            <div class="metric-value">
                {full_slope_100:+.2f} °C
            </div>
            <div style="color:#94a3b8; margin-top:8px;">
                100년당 변화량
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    recent_value = (
        f"{recent_slope_100:+.2f} °C"
        if not np.isnan(recent_slope_100)
        else "-"
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">최근 20년</div>
            <div class="metric-value">
                {recent_value}
            </div>
            <div style="color:#94a3b8; margin-top:8px;">
                100년당 변화량으로 환산
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown(
    """
    <div class="info-box">
    기울기는 회귀직선의 기울기를 100배한 값입니다.
    즉, 실제 분석 기간의 변화 속도를 '100년 동안 몇 °C 변하는가'로 표현했습니다.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# MAIN TEMPERATURE GRAPH
# =========================================================
st.markdown(
    '<div class="section-title">🌡️ 서울 연평균 기온 변화</div>',
    unsafe_allow_html=True
)

fig = go.Figure()

# 실제 평균기온
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["평균기온"],
        mode="lines+markers",
        name="실제 연평균 기온",
        hovertemplate=(
            "%{x}년<br>"
            "평균기온: %{y:.2f}°C"
            "<extra></extra>"
        )
    )
)

# 전체 기간 회귀선
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["전체추세"],
        mode="lines",
        name="전체 기간 추세선",
        line=dict(
            dash="dash",
            width=3
        ),
        hovertemplate=(
            "%{x}년<br>"
            "추세: %{y:.2f}°C"
            "<extra></extra>"
        )
    )
)

# 최근 20년 회귀선
if len(recent20) >= 2:

    recent_line_x = np.array([
        recent20["연도"].min(),
        recent20["연도"].max()
    ])

    recent_line_y = (
        recent_slope *
        (recent_line_x - BASE_YEAR)
        + recent_intercept
    )

    fig.add_trace(
        go.Scatter(
            x=recent_line_x,
            y=recent_line_y,
            mode="lines",
            name="최근 20년 추세선",
            line=dict(
                dash="dot",
                width=3
            ),
            hovertemplate=(
                "%{x}년<br>"
                "최근 20년 추세: %{y:.2f}°C"
                "<extra></extra>"
            )
        )
    )


fig.update_layout(
    template="plotly_dark",
    height=600,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#f1f5f9"),
    xaxis=dict(
        title="연도",
        dtick=10,
        gridcolor="#30363d"
    ),
    yaxis=dict(
        title="평균기온 (°C)",
        gridcolor="#30363d"
    ),
    legend=dict(
        bgcolor="#161b22"
    ),
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================================================
# WARMEST / COLDEST YEAR
# =========================================================
st.markdown(
    '<div class="section-title">🔥 가장 따뜻했던 해와 가장 추웠던 해</div>',
    unsafe_allow_html=True
)

warmest = annual.loc[
    annual["평균기온"].idxmax()
]

coldest = annual.loc[
    annual["평균기온"].idxmin()
]

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">🔥 가장 따뜻했던 해</div>
            <div class="metric-value">
                {int(warmest["연도"])}년
            </div>
            <div style="color:#94a3b8;">
                평균 {warmest["평균기온"]:.2f}°C
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">❄️ 가장 추웠던 해</div>
            <div class="metric-value">
                {int(coldest["연도"])}년
            </div>
            <div style="color:#94a3b8;">
                평균 {coldest["평균기온"]:.2f}°C
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# ANNUAL TEMPERATURE RANGE
# =========================================================
st.markdown(
    '<div class="section-title">📏 연도별 평균기온 범위</div>',
    unsafe_allow_html=True
)

fig_range = go.Figure()

fig_range.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["최고기온"],
        mode="lines",
        name="높은 값",
        line=dict(width=1)
    )
)

fig_range.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["최저기온"],
        mode="lines",
        name="낮은 값",
        fill="tonexty",
        line=dict(width=1)
    )
)

fig_range.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["평균기온"],
        mode="lines",
        name="평균",
        line=dict(width=3)
    )
)

fig_range.update_layout(
    template="plotly_dark",
    height=500,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#f1f5f9"),
    xaxis=dict(
        title="연도",
        dtick=10,
        gridcolor="#30363d"
    ),
    yaxis=dict(
        title="기온 (°C)",
        gridcolor="#30363d"
    )
)

st.plotly_chart(
    fig_range,
    use_container_width=True
)


# =========================================================
# FUTURE TEMPERATURE PREDICTION
# =========================================================
st.markdown(
    '<div class="section-title">🔮 미래 기온 예측</div>',
    unsafe_allow_html=True
)

max_prediction_year = int(annual["연도"].max()) + 50

selected_year = st.slider(
    "예측할 연도",
    min_value=int(annual["연도"].min()),
    max_value=max_prediction_year,
    value=int(annual["연도"].max()) + 10,
    step=1
)

predicted_temperature = (
    full_slope *
    (selected_year - BASE_YEAR)
    + full_intercept
)

st.markdown(
    f"""
    <div class="prediction-box">
        <div class="prediction-year">
            {selected_year}년 예상 연평균 기온
        </div>
        <div class="prediction-value">
            {predicted_temperature:.2f} °C
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# PREDICTION GRAPH
# =========================================================
future_years = np.arange(
    annual["연도"].min(),
    max_prediction_year + 1
)

future_predictions = (
    full_slope *
    (future_years - BASE_YEAR)
    + full_intercept
)

fig_future = go.Figure()

fig_future.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["평균기온"],
        mode="markers",
        name="실제 평균기온",
        marker=dict(size=6)
    )
)

fig_future.add_trace(
    go.Scatter(
        x=future_years,
        y=future_predictions,
        mode="lines",
        name="회귀 기반 예측",
        line=dict(
            dash="dash",
            width=3
        )
    )
)

fig_future.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temperature],
        mode="markers",
        name="선택한 연도",
        marker=dict(
            size=16
        )
    )
)

fig_future.update_layout(
    template="plotly_dark",
    height=500,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#f1f5f9"),
    xaxis=dict(
        title="연도",
        gridcolor="#30363d"
    ),
    yaxis=dict(
        title="평균기온 (°C)",
        gridcolor="#30363d"
    )
)

st.plotly_chart(
    fig_future,
    use_container_width=True
)


# =========================================================
# UNUSUAL YEARS
# =========================================================
st.markdown(
    '<div class="section-title">⚠️ 평년과 차이가 큰 연도</div>',
    unsafe_allow_html=True
)

annual["추세와의 차이"] = (
    annual["평균기온"] - annual["전체추세"]
)

annual["절대차이"] = annual["추세와의 차이"].abs()

abnormal = (
    annual
    .sort_values("절대차이", ascending=False)
    .head(10)
    .sort_values("연도")
)

fig_abnormal = px.bar(
    abnormal,
    x="연도",
    y="추세와의 차이",
    title="회귀 추세선에서 크게 벗어난 연도",
    hover_data={
        "연도": True,
        "평균기온": ":.2f",
        "추세와의 차이": ":.2f"
    }
)

fig_abnormal.update_layout(
    template="plotly_dark",
    height=450,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#f1f5f9"),
    xaxis=dict(
        title="연도",
        gridcolor="#30363d"
    ),
    yaxis=dict(
        title="추세와의 차이 (°C)",
        gridcolor="#30363d"
    )
)

st.plotly_chart(
    fig_abnormal,
    use_container_width=True
)


# =========================================================
# DATA QUALITY
# =========================================================
st.markdown(
    '<div class="section-title">🔎 데이터 품질</div>',
    unsafe_allow_html=True
)

total_rows = len(df)
missing_date = df["날짜"].isna().sum()
missing_temp = df["평균기온"].isna().sum()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "전체 관측 행",
        f"{total_rows:,}"
    )

with col2:
    st.metric(
        "날짜 결측",
        f"{missing_date:,}"
    )

with col3:
    st.metric(
        "평균기온 결측",
        f"{missing_temp:,}"
    )

with col4:
    st.metric(
        "최종 분석 연도 수",
        f"{len(annual):,}"
    )


# =========================================================
# ANNUAL DATA TABLE
# =========================================================
with st.expander("📋 연도별 분석 데이터 보기"):

    display_df = annual[
        [
            "연도",
            "평균기온",
            "관측일수",
            "최저기온",
            "최고기온"
        ]
    ].copy()

    display_df["평균기온"] = display_df["평균기온"].round(2)
    display_df["최저기온"] = display_df["최저기온"].round(2)
    display_df["최고기온"] = display_df["최고기온"].round(2)

    display_df.columns = [
        "연도",
        "평균기온 (°C)",
        "관측일수",
        "최저 평균기온 (°C)",
        "최고 평균기온 (°C)"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# METHOD
# =========================================================
with st.expander("ℹ️ 어떻게 계산했나요?"):

    st.markdown(
        f"""
        ### 분석 방법

        1. 서울 기온 데이터를 불러옵니다.

        2. 날짜를 `YYYY-MM-DD` 형식으로 변환합니다.

        3. **2025년 이하의 데이터만** 사용합니다.

        4. 한 해에 평균기온 관측일이 **300일 이상인 연도만**
           분석에 사용합니다.

        5. 각 연도의 `평균기온`을 계산합니다.

        6. 회귀분석의 독립변수는 실제 연도 자체가 아니라

        **`연도 - {BASE_YEAR}`**

        로 설정했습니다.

        7. 전체 기간의 회귀직선 기울기를 계산합니다.

        8. 기울기에 100을 곱해

        **"100년에 몇 °C 변하는가"**

        로 표시합니다.

        9. 마지막 20년의 데이터만 따로 사용해
           최근 20년의 변화 속도도 계산합니다.

        10. 미래 예측값은 **전체 기간의 회귀직선**을
            미래 연도까지 연장해서 계산합니다.

        ### 주의

        이 예측값은 과거 데이터의 선형 추세를 단순히 연장한 값입니다.
        실제 미래의 기온을 정확하게 예측한다는 의미는 아닙니다.
        """
    )


# =========================================================
# FOOTER
# =========================================================
st.markdown(
    """
    <div style="
        text-align:center;
        color:#64748b;
        padding:30px 0 10px 0;
        font-size:13px;
    ">
        서울 기온 데이터 기반 분석 · 2025년까지의 데이터 사용
    </div>
    """,
    unsafe_allow_html=True
)
