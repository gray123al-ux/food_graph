import streamlit as st
import pandas as pd
import requests
from datetime import date
import plotly.express as px


# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="급식의 한 달 평균 칼로리는 얼마나 될까?",
    page_icon="🍚",
    layout="wide"
)


# =========================================================
# 다크 모드 스타일
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

    .info-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
    }

    .info-title {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 5px;
    }

    .info-value {
        color: #f8fafc;
        font-size: 25px;
        font-weight: 700;
    }

    .big-calorie {
        background: #172033;
        border: 1px solid #3b82f6;
        border-radius: 18px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    }

    .big-calorie-label {
        color: #93c5fd;
        font-size: 17px;
    }

    .big-calorie-value {
        color: white;
        font-size: 48px;
        font-weight: 800;
        margin-top: 8px;
    }

    .section-title {
        font-size: 26px;
        font-weight: 700;
        margin-top: 35px;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 제목
# =========================================================
st.markdown(
    '<div class="main-title">🍚 급식의 한 달 평균 칼로리는 얼마나 될까?</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '송탄고등학교의 실제 급식 데이터를 이용해 하루 급식 칼로리와 월 평균 칼로리를 살펴봅니다.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# 학교 정보
# =========================================================
교육청코드 = "J10"
학교코드 = "7530480"
학교명 = "송탄고등학교"
식사코드 = "2"

API_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


# =========================================================
# NEIS 인증키 확인
# =========================================================
if "NEIS_KEY" not in st.secrets:

    st.error(
        "NEIS_KEY가 Streamlit Secrets에 설정되어 있지 않습니다."
    )

    st.info(
        """
        Streamlit의 Secrets에 다음과 같이 입력하세요.

        NEIS_KEY = "발급받은_인증키"
        """
    )

    st.stop()


NEIS_KEY = st.secrets["NEIS_KEY"]


# =========================================================
# NEIS 급식 데이터 가져오기
# =========================================================
@st.cache_data(ttl=3600)
def 급식데이터가져오기(시작일, 종료일):

    params = {
        "KEY": NEIS_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,

        "ATPT_OFCDC_SC_CODE": 교육청코드,
        "SD_SCHUL_CODE": 학교코드,

        "MLSV_FROM_YMD": 시작일,
        "MLSV_TO_YMD": 종료일,

        "MMEAL_SC_CODE": 식사코드
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if "mealServiceDietInfo" not in data:
        return pd.DataFrame()

    급식정보 = data["mealServiceDietInfo"]

    if len(급식정보) < 2:
        return pd.DataFrame()

    rows = 급식정보[1].get("row", [])

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


# =========================================================
# 사이드바
# =========================================================
st.sidebar.title("⚙️ 분석 설정")

st.sidebar.write(
    f"**학교:** {학교명}"
)

st.sidebar.write(
    "**식사:** 중식"
)

st.sidebar.write(
    "**교육청:** 경기도교육청"
)


# =========================================================
# 연도 선택
# =========================================================
현재연도 = date.today().year

선택연도 = st.sidebar.selectbox(
    "연도 선택",
    list(range(2020, 현재연도 + 1)),
    index=현재연도 - 2020
)


# =========================================================
# 월 선택
# =========================================================
선택월 = st.sidebar.selectbox(
    "월 선택",
    list(range(1, 13)),
    index=date.today().month - 1
)


# =========================================================
# 선택한 달의 시작일과 마지막 날짜 계산
# =========================================================
시작일 = f"{선택연도}{선택월:02d}01"

if 선택월 == 12:
    다음연도 = 선택연도 + 1
    다음월 = 1
else:
    다음연도 = 선택연도
    다음월 = 선택월 + 1


다음달첫날 = pd.Timestamp(
    f"{다음연도}-{다음월:02d}-01"
)

마지막날 = 다음달첫날 - pd.Timedelta(days=1)

종료일 = 마지막날.strftime("%Y%m%d")


# =========================================================
# 데이터 가져오기
# =========================================================
with st.spinner("급식 데이터를 불러오는 중입니다..."):

    try:

        df = 급식데이터가져오기(
            시작일,
            종료일
        )

    except requests.exceptions.RequestException as e:

        st.error(
            "NEIS 급식 API에 연결할 수 없습니다."
        )

        st.exception(e)

        st.stop()

    except Exception as e:

        st.error(
            "데이터를 불러오는 중 오류가 발생했습니다."
        )

        st.exception(e)

        st.stop()


# =========================================================
# 데이터가 없는 경우
# =========================================================
if df.empty:

    st.warning(
        f"{선택연도}년 {선택월}월의 급식 데이터가 없습니다."
    )

    st.stop()


# =========================================================
# 데이터 정리
# =========================================================

# 날짜 변환
df["MLSV_YMD"] = pd.to_datetime(
    df["MLSV_YMD"],
    format="%Y%m%d",
    errors="coerce"
)


# 칼로리 숫자 변환
# 예: "748.1 Kcal" → 748.1
df["CAL_INFO"] = (
    df["CAL_INFO"]
    .astype(str)
    .str.extract(r"([\d.]+)", expand=False)
)

df["CAL_INFO"] = pd.to_numeric(
    df["CAL_INFO"],
    errors="coerce"
)


# 날짜순 정렬
df = df.sort_values(
    "MLSV_YMD"
).reset_index(drop=True)


# =========================================================
# 기본 통계
# =========================================================
평균칼로리 = df["CAL_INFO"].mean()

최고칼로리 = df["CAL_INFO"].max()

최저칼로리 = df["CAL_INFO"].min()

급식일수 = df["CAL_INFO"].notna().sum()


# =========================================================
# 학교 정보
# =========================================================
st.markdown(
    '<div class="section-title">🏫 학교 정보</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">학교</div>
            <div class="info-value">
                {학교명}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">선택 연도</div>
            <div class="info-value">
                {선택연도}년
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">선택 월</div>
            <div class="info-value">
                {선택월}월
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">급식이 제공된 날</div>
            <div class="info-value">
                {급식일수}일
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 월 평균 칼로리
# =========================================================
st.markdown(
    '<div class="section-title">🔥 이 달의 평균 칼로리</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="big-calorie">
        <div class="big-calorie-label">
            {선택연도}년 {선택월}월 점심 급식 평균
        </div>

        <div class="big-calorie-value">
            {평균칼로리:,.1f} kcal
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 통계 카드
# =========================================================
col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "평균 칼로리",
        f"{평균칼로리:,.1f} kcal"
    )


with col2:

    st.metric(
        "가장 높은 칼로리",
        f"{최고칼로리:,.1f} kcal"
    )


with col3:

    st.metric(
        "가장 낮은 칼로리",
        f"{최저칼로리:,.1f} kcal"
    )


# =========================================================
# 그래프 1
# 일별 급식 칼로리
# =========================================================
st.markdown(
    '<div class="section-title">📈 날짜별 급식 칼로리</div>',
    unsafe_allow_html=True
)

fig_daily = px.line(
    df,
    x="MLSV_YMD",
    y="CAL_INFO",
    markers=True,
    labels={
        "MLSV_YMD": "날짜",
        "CAL_INFO": "칼로리 (kcal)"
    },
    title=f"{선택연도}년 {선택월}월 날짜별 급식 칼로리"
)

fig_daily.update_layout(
    template="plotly_dark",
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#f1f5f9"),
    height=500
)

st.plotly_chart(
    fig_daily,
    use_container_width=True
)


st.info(
    "이 그래프를 보면 날짜에 따라 급식의 칼로리가 어떻게 달라지는지 알 수 있습니다."
)


# =========================================================
# 그래프 2
# 날짜별 칼로리 막대그래프
# =========================================================
st.markdown(
    '<div class="section-title">🍱 날짜별 칼로리 비교</div>',
    unsafe_allow_html=True
)

fig_bar = px.bar(
    df,
    x="MLSV_YMD",
    y="CAL_INFO",
    labels={
        "MLSV_YMD": "날짜",
        "CAL_INFO": "칼로리 (kcal)"
    },
    title=f"{선택연도}년 {선택월}월 급식 칼로리 비교"
)

fig_bar.update_layout(
    template="plotly_dark",
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#f1f5f9"),
    height=500
)

st.plotly_chart(
    fig_bar,
    use_container_width=True
)


st.info(
    "막대의 높이를 비교하면 어느 날의 급식 칼로리가 높은지 쉽게 확인할 수 있습니다."
)


# =========================================================
# 급식 메뉴 표
# =========================================================
st.markdown(
    '<div class="section-title">🍽️ 날짜별 급식 메뉴</div>',
    unsafe_allow_html=True
)


표시데이터 = df[
    [
        "MLSV_YMD",
        "DDISH_NM",
        "CAL_INFO"
    ]
].copy()


표시데이터["MLSV_YMD"] = (
    표시데이터["MLSV_YMD"]
    .dt.strftime("%Y-%m-%d")
)


표시데이터.columns = [
    "날짜",
    "급식 메뉴",
    "칼로리 (kcal)"
]


st.dataframe(
    표시데이터,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 가장 높은 / 낮은 칼로리
# =========================================================
st.markdown(
    '<div class="section-title">🔎 가장 높은 날과 가장 낮은 날</div>',
    unsafe_allow_html=True
)


최고칼로리행 = df.loc[
    df["CAL_INFO"].idxmax()
]

최저칼로리행 = df.loc[
    df["CAL_INFO"].idxmin()
]


col1, col2 = st.columns(2)


with col1:

    st.markdown(
        f"""
        <div class="info-card">

            <div class="info-title">
                🔥 가장 높은 칼로리
            </div>

            <div class="info-value">
                {최고칼로리행["CAL_INFO"]:,.1f} kcal
            </div>

            <div style="color:#94a3b8; margin-top:8px;">
                {최고칼로리행["MLSV_YMD"].strftime("%Y-%m-%d")}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="info-card">

            <div class="info-title">
                🌱 가장 낮은 칼로리
            </div>

            <div class="info-value">
                {최저칼로리행["CAL_INFO"]:,.1f} kcal
            </div>

            <div style="color:#94a3b8; margin-top:8px;">
                {최저칼로리행["MLSV_YMD"].strftime("%Y-%m-%d")}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 데이터 설명
# =========================================================
with st.expander("ℹ️ 데이터와 계산 방법"):

    st.markdown(
        f"""
        ### 데이터 출처

        이 앱은 **NEIS 교육정보 개방 포털의 급식식단정보 API**를
        사용합니다.

        ### 학교

        **{학교명}**

        - 교육청 코드: `{교육청코드}`
        - 학교 코드: `{학교코드}`
        - 식사 코드: `{식사코드}` — 중식

        ### 칼로리 계산

        NEIS에서 제공하는 `CAL_INFO` 값을 사용합니다.

        예를 들어 API에서

        `748.1 Kcal`

        로 제공되는 값은

        `748.1 kcal`

        로 변환하여 그래프에 사용합니다.

        ### 월 평균

        선택한 달에 실제로 제공된 급식의 칼로리를 모두 이용하여
        평균을 계산합니다.

        즉,

        **월 평균 칼로리 = 해당 월 급식 칼로리의 합 ÷ 급식이 제공된 날의 수**

        입니다.
        """
    )


# =========================================================
# 푸터
# =========================================================
st.markdown(
    """
    <div style="
        text-align:center;
        color:#64748b;
        padding:35px 0 10px 0;
        font-size:13px;
    ">
        🍚 급식 칼로리 분석 · NEIS 교육정보 개방 포털 API
    </div>
    """,
    unsafe_allow_html=True
)
