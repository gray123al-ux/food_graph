```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 기온 예측기")
st.write("서울의 과거 기온 데이터를 이용해 연평균 기온의 변화 추세를 살펴보고 미래 기온을 예측합니다.")

# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")
    df["최저기온"] = pd.to_numeric(df["최저기온"], errors="coerce")
    df["최고기온"] = pd.to_numeric(df["최고기온"], errors="coerce")

    return df


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()


# --------------------------------------------------
# 연도 만들기
# --------------------------------------------------
df["연도"] = df["날짜"].dt.year

# 2025년까지만 사용
df = df[df["연도"] <= 2025].copy()

# --------------------------------------------------
# 연도별 관측일 수 계산
# 평균기온이 실제로 존재하는 날짜만 계산
# --------------------------------------------------
year_count = (
    df.dropna(subset=["평균기온"])
    .groupby("연도")
    .size()
)

# 300일 이상 관측된 연도만 사용
valid_years = year_count[year_count >= 300].index

df_valid = df[df["연도"].isin(valid_years)].copy()


# --------------------------------------------------
# 연평균 기온 계산
# --------------------------------------------------
annual = (
    df_valid
    .dropna(subset=["평균기온"])
    .groupby("연도", as_index=False)
    .agg(
        연평균기온=("평균기온", "mean"),
        관측일수=("평균기온", "count")
    )
)

annual = annual.sort_values("연도").reset_index(drop=True)

if len(annual) < 2:
    st.error("회귀분석을 수행할 충분한 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 회귀분석
# 독립변수 = 1908년부터 몇 년이 지났는가
# --------------------------------------------------
BASE_YEAR = 1908

annual["경과연수"] = annual["연도"] - BASE_YEAR

x = annual["경과연수"].to_numpy()
y = annual["연평균기온"].to_numpy()

slope, intercept = np.polyfit(x, y, 1)

annual["회귀예측기온"] = slope * x + intercept

# 상관계수
correlation = np.corrcoef(x, y)[0, 1]

# 100년당 상승 폭
slope_100 = slope * 100


# --------------------------------------------------
# 최근 20년 회귀분석
# --------------------------------------------------
latest_year = annual["연도"].max()
recent_start_year = latest_year - 19

recent = annual[annual["연도"] >= recent_start_year].copy()

if len(recent) >= 2:
    recent_x = (recent["연도"] - BASE_YEAR).to_numpy()
    recent_y = recent["연평균기온"].to_numpy()

    recent_slope, recent_intercept = np.polyfit(
        recent_x,
        recent_y,
        1
    )

    recent_slope_100 = recent_slope * 100

    recent["회귀예측기온"] = (
        recent_slope * recent_x + recent_intercept
    )
else:
    recent_slope_100 = np.nan


# --------------------------------------------------
# 핵심 결과
# --------------------------------------------------
st.subheader("📈 기온 변화의 핵심 결과")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "분석 기간",
        f"{annual['연도'].min()}~{annual['연도'].max()}"
    )

with col2:
    st.metric(
        "상관계수",
        f"{correlation:.3f}"
    )

with col3:
    st.metric(
        "100년에 몇 °C 오르는가?",
        f"{slope_100:+.2f} °C"
    )


# --------------------------------------------------
# 전체 기간 vs 최근 20년
# --------------------------------------------------
st.subheader("🌡️ 기온 상승 속도 비교")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 전체 기간")
    st.metric(
        "100년당 기온 변화",
        f"{slope_100:+.2f} °C"
    )
    st.caption(
        f"{annual['연도'].min()}~{annual['연도'].max()}년의 "
        "연평균 기온을 이용한 회귀분석"
    )

with col2:
    st.markdown("### 최근 20년")
    if not np.isnan(recent_slope_100):
        st.metric(
            "100년당 기온 변화",
            f"{recent_slope_100:+.2f} °C"
        )
        st.caption(
            f"{recent_start_year}~{latest_year}년의 "
            "연평균 기온을 이용한 회귀분석"
        )
    else:
        st.warning("최근 20년 회귀분석을 위한 데이터가 부족합니다.")


# --------------------------------------------------
# 연평균 기온 + 회귀선
# --------------------------------------------------
st.subheader("📊 서울 연평균 기온 변화")

fig = go.Figure()

# 실제 연평균 기온
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연평균기온"],
        mode="markers",
        name="실제 연평균 기온",
        text=[
            f"{year}년<br>"
            f"평균기온: {temp:.2f}°C<br>"
            f"관측일수: {days}일"
            for year, temp, days in zip(
                annual["연도"],
                annual["연평균기온"],
                annual["관측일수"]
            )
        ],
        hovertemplate="%{text}<extra></extra>"
    )
)

# 전체 기간 회귀선
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["회귀예측기온"],
        mode="lines",
        name="전체 기간 회귀선"
    )
)

# 최근 20년 회귀선
if len(recent) >= 2:
    fig.add_trace(
        go.Scatter(
            x=recent["연도"],
            y=recent["회귀예측기온"],
            mode="lines",
            name="최근 20년 회귀선",
            line=dict(dash="dash")
        )
    )

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균 기온 (°C)",
    hovermode="x unified",
    height=550
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "이 그래프에서는 서울의 연평균 기온이 장기적으로 어떻게 변해왔는지와 "
    "전체 기간 및 최근 20년의 추세선을 함께 비교할 수 있습니다."
)


# --------------------------------------------------
# 연도 슬라이더를 이용한 기온 예측
# --------------------------------------------------
st.subheader("🔮 연도를 선택해서 기온 예측하기")

min_year = int(annual["연도"].min())
max_year = int(annual["연도"].max())

future_max_year = max_year + 50

selected_year = st.slider(
    "예측할 연도",
    min_value=min_year,
    max_value=future_max_year,
    value=max_year,
    step=1
)

selected_x = selected_year - BASE_YEAR

predicted_temp = slope * selected_x + intercept

st.markdown(
    f"""
    <div style="
        background-color:#f0f7ff;
        padding:30px;
        border-radius:15px;
        text-align:center;
        margin:20px 0;
    ">
        <div style="font-size:22px;">
            {selected_year}년 예상 연평균 기온
        </div>
        <div style="
            font-size:52px;
            font-weight:bold;
            margin-top:10px;
        ">
            {predicted_temp:.2f} °C
        </div>
        <div style="font-size:16px; color:#666;">
            전체 기간의 선형 회귀 추세를 이용한 계산값
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# 예측 그래프
# --------------------------------------------------
st.subheader("🔮 과거 데이터와 미래 예측")

prediction_years = np.arange(
    min_year,
    future_max_year + 1
)

prediction_x = prediction_years - BASE_YEAR

prediction_temps = (
    slope * prediction_x + intercept
)

prediction_df = pd.DataFrame({
    "연도": prediction_years,
    "예측기온": prediction_temps
})

fig2 = go.Figure()

# 실제 데이터
fig2.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연평균기온"],
        mode="markers",
        name="실제 연평균 기온"
    )
)

# 회귀 기반 예측
fig2.add_trace(
    go.Scatter(
        x=prediction_df["연도"],
        y=prediction_df["예측기온"],
        mode="lines",
        name="회귀 기반 예측"
    )
)

# 선택된 연도 표시
fig2.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temp],
        mode="markers",
        marker=dict(size=14),
        name=f"{selected_year}년 예측"
    )
)

fig2.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균 기온 (°C)",
    hovermode="x unified",
    height=500
)

st.plotly_chart(fig2, use_container_width=True)


# --------------------------------------------------
# 데이터 정보
# --------------------------------------------------
st.subheader("📋 분석에 사용한 데이터")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "사용한 연도 수",
        f"{len(annual)}년"
    )

with col2:
    st.metric(
        "최초 연도",
        f"{annual['연도'].min()}년"
    )

with col3:
    st.metric(
        "마지막 연도",
        f"{annual['연도'].max()}년"
    )


# --------------------------------------------------
# 연도별 데이터 표
# --------------------------------------------------
with st.expander("연도별 연평균 기온 데이터 보기"):
    display_df = annual[
        ["연도", "연평균기온", "관측일수"]
    ].copy()

    display_df["연평균기온"] = display_df["연평균기온"].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 분석 방법 설명
# --------------------------------------------------
with st.expander("ℹ️ 어떻게 계산했나요?"):
    st.markdown(
        """
        **1. 서울 기온 데이터를 불러옵니다.**

        서울의 일별 평균기온 데이터를 사용합니다.

        **2. 연도별 평균을 계산합니다.**

        각 연도의 일별 평균기온을 평균내어 연평균 기온을 구합니다.

        **3. 관측일수가 300일 미만인 연도는 제외합니다.**

        데이터가 지나치게 적은 연도가 회귀분석에 영향을 주지 않도록 했습니다.

        **4. 2025년 이후 데이터는 제외합니다.**

        2025년까지를 분석 기준 기간으로 사용합니다.

        **5. 선형 회귀를 계산합니다.**

        독립변수는 단순한 연도가 아니라

        `연도 - 1908`

        로 계산했습니다.

        **6. 기울기를 100년 기준으로 환산합니다.**

        예를 들어 회귀선의 기울기가 `0.015`라면,

        `0.015 × 100 = 1.5`

        이므로 **100년에 약 1.5°C 변화**한다고 해석합니다.

        **주의:** 이 값은 과거 데이터의 선형 추세를 미래까지 그대로 연장한
        통계적 예측이며, 실제 미래 기온을 보장하는 예측은 아닙니다.
        """
    )
```

`requirements.txt`는 다음처럼 두면 됩니다.

```text
streamlit
pandas
numpy
plotly
```

이 코드는 **전체 기간의 100년당 변화량**과 **최근 20년의 100년당 변화량**을 나란히 보여주고, 선택한 연도의 회귀 기반 예상 기온까지 표시합니다.
