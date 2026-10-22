import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone


# ============================================================
# 1. 기본 설정
# ============================================================

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("KOBIS 영화관입장권통합전산망 일별 박스오피스")


# ============================================================
# 2. 한국 시간 기준으로 '어제' 계산하기
# ============================================================

# 한국은 UTC보다 9시간 빠릅니다.
# 서버가 한국에 있지 않아도 한국 시간으로 계산할 수 있습니다.
KST = timezone(timedelta(hours=9))

now_kst = datetime.now(KST)
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 보여줄 날짜 형식
display_date = yesterday.strftime("%Y년 %m월 %d일")


# ============================================================
# 3. KOBIS 인증키 가져오기
# ============================================================

# Streamlit Cloud의 Secrets에
# KOBIS_KEY = "발급받은 인증키"
# 형태로 저장해야 합니다.
#
# 인증키를 코드에 직접 작성하지 않습니다.

try:
    kobis_key = st.secrets["KOBIS_KEY"]
except Exception:
    st.error("🔑 KOBIS 인증키를 찾을 수 없습니다.")

    st.info(
        """
        **확인할 사항**

        1. Streamlit Cloud에서 앱의 **Settings → Secrets**로 이동했는지 확인하세요.
        2. 아래처럼 입력했는지 확인하세요.

        `KOBIS_KEY = "발급받은 인증키"`

        3. `KOBIS_KEY`의 철자와 대소문자가 정확한지 확인하세요.
        4. 인증키를 `main.py` 코드에 직접 넣을 필요는 없습니다.
        """
    )

    st.stop()


# ============================================================
# 4. KOBIS API 주소
# ============================================================

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# ============================================================
# 5. KOBIS API 요청
# ============================================================

params = {
    "key": kobis_key,
    "targetDt": target_date
}


try:
    response = requests.get(
        API_URL,
        params=params,
        timeout=15
    )

except requests.exceptions.Timeout:
    st.error("⏰ KOBIS API 요청 시간이 초과되었습니다.")

    st.info(
        """
        **확인할 사항**

        - 인터넷 연결이 정상인지 확인하세요.
        - 잠시 후 앱을 다시 실행해 보세요.
        - KOBIS 서버가 일시적으로 응답하지 않는 상황일 수도 있습니다.
        """
    )

    st.stop()

except requests.exceptions.RequestException as e:
    st.error("🌐 KOBIS API에 접속하지 못했습니다.")

    st.info(
        """
        **확인할 사항**

        - KOBIS API 주소가 정상적으로 접속되는지 확인하세요.
        - 인터넷 연결 상태를 확인하세요.
        - 잠시 후 다시 시도해 보세요.
        """
    )

    st.stop()


# ============================================================
# 6. HTTP 응답 상태 확인
# ============================================================

if response.status_code != 200:
    st.error(
        f"❌ KOBIS API 요청에 실패했습니다. "
        f"(HTTP 상태 코드: {response.status_code})"
    )

    st.info(
        """
        **확인할 사항**

        - KOBIS API 서버 상태를 확인하세요.
        - 잠시 후 다시 실행해 보세요.
        - API 주소가 변경되지 않았는지 확인하세요.
        """
    )

    st.stop()


# ============================================================
# 7. JSON 데이터로 변환
# ============================================================

try:
    data = response.json()

except ValueError:
    st.error("❌ KOBIS API에서 올바른 JSON 데이터를 받지 못했습니다.")

    st.info(
        """
        **확인할 사항**

        - KOBIS API 서버의 응답 상태를 확인하세요.
        - 잠시 후 다시 실행해 보세요.
        """
    )

    st.stop()


# ============================================================
# 8. KOBIS faultInfo 확인
# ============================================================

# KOBIS는 인증키가 잘못되어도 HTTP 상태 코드가 200일 수 있습니다.
# 이 경우 boxOfficeResult가 아니라 faultInfo가 들어옵니다.

if "faultInfo" in data:

    fault_info = data.get("faultInfo", {})

    error_code = fault_info.get("message", "알 수 없는 오류")
    error_detail = fault_info.get("code", "")

    st.error("🔑 KOBIS API에서 오류를 반환했습니다.")

    if error_detail:
        st.write(f"**오류 코드:** `{error_detail}`")

    st.write(f"**오류 내용:** {error_code}")

    st.info(
        """
        **확인할 사항**

        1. Streamlit Cloud의 **Settings → Secrets**에서
           `KOBIS_KEY`가 정확하게 입력되어 있는지 확인하세요.
        2. 인증키 앞뒤에 불필요한 공백이 없는지 확인하세요.
        3. KOBIS에서 발급받은 API 인증키가 유효한지 확인하세요.
        4. API 사용이 제한되었거나 호출량을 초과하지 않았는지 확인하세요.
        """
    )

    st.stop()


# ============================================================
# 9. boxOfficeResult 확인
# ============================================================

if "boxOfficeResult" not in data:

    st.error("❌ KOBIS API 응답에서 박스오피스 데이터를 찾을 수 없습니다.")

    st.info(
        """
        **확인할 사항**

        - KOBIS API 응답 형식이 변경되었는지 확인하세요.
        - 조회 날짜가 정상적으로 계산되었는지 확인하세요.
        - 잠시 후 다시 실행해 보세요.
        """
    )

    st.stop()


box_office_result = data["boxOfficeResult"]

movie_list = box_office_result.get("dailyBoxOfficeList", [])


# ============================================================
# 10. 영화 목록이 비어 있는지 확인
# ============================================================

if not movie_list:

    st.warning("🎬 조회된 영화 목록이 없습니다.")

    st.info(
        f"""
        현재 조회 날짜는 **{display_date}**입니다.

        **확인할 사항**

        - KOBIS에 해당 날짜의 박스오피스 자료가 등록되었는지 확인하세요.
        - 조회 날짜가 휴일이나 자료 집계가 늦어지는 날짜인지 확인하세요.
        - KOBIS API가 정상적으로 응답하는지 확인하세요.
        - 잠시 후 다시 실행해 보세요.
        """
    )

    st.stop()


# ============================================================
# 11. 필요한 데이터만 표로 정리
# ============================================================

rows = []

for movie in movie_list:

    # KOBIS에서 숫자도 문자열로 보내므로 int로 변환합니다.
    try:
        rank = int(movie.get("rank", 0))
    except (ValueError, TypeError):
        rank = 0

    try:
        audi_cnt = int(movie.get("audiCnt", 0))
    except (ValueError, TypeError):
        audi_cnt = 0

    try:
        audi_acc = int(movie.get("audiAcc", 0))
    except (ValueError, TypeError):
        audi_acc = 0

    try:
        scrn_cnt = int(movie.get("scrnCnt", 0))
    except (ValueError, TypeError):
        scrn_cnt = 0

    rows.append(
        {
            "순위": rank,
            "영화명": movie.get("movieNm", "정보 없음"),
            "개봉일": movie.get("openDt", "정보 없음"),
            "관객수": audi_cnt,
            "누적관객": audi_acc,
            "스크린수": scrn_cnt
        }
    )


df = pd.DataFrame(rows)


# 순위순으로 정렬
df = df.sort_values("순위").reset_index(drop=True)


# ============================================================
# 12. 1위 영화 정보
# ============================================================

first_movie = df.iloc[0]

first_movie_name = first_movie["영화명"]
first_audience = first_movie["관객수"]
first_total_audience = first_movie["누적관객"]
first_screens = first_movie["스크린수"]


# ============================================================
# 13. 조회 날짜 표시
# ============================================================

st.subheader(f"📅 {display_date} 박스오피스")

st.caption(
    f"한국 시간 기준 조회일: {target_date} · "
    f"KOBIS 일별 박스오피스"
)


# ============================================================
# 14. 1위 영화 제목 크게 표시
# ============================================================

st.markdown(
    f"## 🥇 1위: {first_movie_name}"
)


# ============================================================
# 15. 1위 영화 지표 카드 3개
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎟️ 관객수",
        value=f"{first_audience:,}명"
    )

with col2:
    st.metric(
        label="👥 누적관객",
        value=f"{first_total_audience:,}명"
    )

with col3:
    st.metric(
        label="🎬 스크린수",
        value=f"{first_screens:,}개"
    )


# ============================================================
# 16. 관객수 상위 5편 막대그래프
# ============================================================

st.subheader("📊 관객수 상위 5편")

top5 = df.head(5).copy()

# 그래프에서 1위가 위쪽에 보이도록 순서를 뒤집습니다.
top5_chart = top5.sort_values("관객수", ascending=True)

fig = px.bar(
    top5_chart,
    x="관객수",
    y="영화명",
    orientation="h",
    text="관객수",
    labels={
        "관객수": "관객수(명)",
        "영화명": "영화"
    }
)

fig.update_traces(
    texttemplate="%{text:,}명",
    textposition="outside"
)

fig.update_layout(
    height=400,
    margin=dict(l=20, r=80, t=20, b=20)
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 17. 전체 박스오피스 표
# ============================================================

st.subheader("🎥 전체 박스오피스")

# 화면에 표시할 때 숫자를 보기 편하게 만듭니다.
display_df = df.copy()

display_df["관객수"] = display_df["관객수"].map(
    lambda x: f"{x:,}"
)

display_df["누적관객"] = display_df["누적관객"].map(
    lambda x: f"{x:,}"
)

display_df["스크린수"] = display_df["스크린수"].map(
    lambda x: f"{x:,}"
)

st.dataframe(
    display_df[
        [
            "순위",
            "영화명",
            "개봉일",
            "관객수",
            "누적관객",
            "스크린수"
        ]
    ],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 18. 데이터 출처
# ============================================================

st.caption(
    "데이터 출처: 영화관입장권통합전산망(KOBIS) 일별 박스오피스 Open API"
)
