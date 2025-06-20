import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        tabs = st.tabs([
            "1. 결측치 및 중복 확인",
            "2. 연도별 전체 인구 추이 그래프",
            "3. 지역별 인구 변화량 순위",
            "4. 증감률 상위 지역 및 연도 도출",
            "5. 누적영역그래프 등 적절한 시각화"
        ])

        # 1. 결측치 및 중복 확인
        with tabs[0]:
            # ‘세종’ 지역 결측치 '-' → 0 치환
            mask_sejong = df['지역'] == '세종'
            df.loc[mask_sejong, :] = df.loc[mask_sejong, :].replace('-', 0)

            # 숫자 변환
            cols_to_numeric = ['인구', '출생아수(명)', '사망자수(명)']
            for col in cols_to_numeric:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # df.info() 출력
            import io
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            # df.describe() 출력
            st.dataframe(df.describe())

        # 2. 데이터셋 설명
        with tabs[1]:
            st.header("🔍 데이터셋 설명")
            st.markdown(f"""
            - **population_trends.csv**: 2011–2012년까지의 시간대별 대여 기록  
            - 총 관측치: {df.shape[0]}개  
            - 주요 변수:
              - **datetime**: 날짜와 시간 (YYYY-MM-DD HH:MM:SS)  
              - **season**: 계절 (1: 봄, 2: 여름, 3: 가을, 4: 겨울)  
              - **holiday**: 공휴일 여부 (0: 평일, 1: 공휴일)  
              - **workingday**: 근무일 여부 (0: 주말/공휴일, 1: 근무일)  
              - **weather**: 날씨 상태  
                - 1: 맑음·부분적으로 흐림  
                - 2: 안개·흐림  
                - 3: 가벼운 비/눈  
                - 4: 폭우/폭설 등  
              - **temp**: 실제 기온 (섭씨)  
              - **atemp**: 체감 온도 (섭씨)  
              - **humidity**: 상대 습도 (%)  
              - **windspeed**: 풍속 (정규화된 값)  
              - **casual**: 비등록 사용자 대여 횟수  
              - **registered**: 등록 사용자 대여 횟수  
              - **count**: 전체 대여 횟수 (casual + registered)
            """)

            st.subheader("1) 데이터 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("2) 기초 통계량 (`df.describe()`)")
            numeric_df = df.select_dtypes(include=[np.number])
            st.dataframe(numeric_df.describe())

            st.subheader("3) 샘플 데이터 (첫 5행)")
            st.dataframe(df.head())

        # 3. 데이터 로드 & 품질 체크
        with tabs[2]:
            st.header("📥 데이터 로드 & 품질 체크")
            st.subheader("결측값 개수")
            missing = df.isnull().sum()
            st.bar_chart(missing)

            duplicates = df.duplicated().sum()
            st.write(f"- 중복 행 개수: {duplicates}개")

        # 4. Datetime 특성 추출
        with tabs[3]:
            st.header("🕒 Datetime 특성 추출")
            st.markdown("`datetime` 컬럼에서 연, 월, 일, 시, 요일 등을 추출합니다.")

            df['year'] = df['datetime'].dt.year
            df['month'] = df['datetime'].dt.month
            df['day'] = df['datetime'].dt.day
            df['hour'] = df['datetime'].dt.hour
            df['dayofweek'] = df['datetime'].dt.dayofweek

            st.subheader("추출된 특성 예시")
            st.dataframe(df[['datetime', 'year', 'month', 'day', 'hour',
                             'dayofweek']].head())

            # --- 요일 숫자 → 요일명 매핑 (참고용) ---
            day_map = {
                0: '월요일',
                1: '화요일',
                2: '수요일',
                3: '목요일',
                4: '금요일',
                5: '토요일',
                6: '일요일'
            }
            st.markdown("**(참고) dayofweek 숫자 → 요일**")
            # 중복 제거 후 정렬하여 표시
            mapping_df = pd.DataFrame({
                'dayofweek': list(day_map.keys()),
                'weekday': list(day_map.values())
            })
            st.dataframe(mapping_df, hide_index=True)

        # 5. 시각화
        with tabs[4]:
            st.header("📈 시각화")
            # by 근무일 여부
            st.subheader("근무일 여부별 시간대별 평균 대여량")
            fig1, ax1 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='workingday', data=df,
                          ax=ax1)
            ax1.set_xlabel("Hour");
            ax1.set_ylabel("Average Count")
            st.pyplot(fig1)
            st.markdown(
                "> **해석:** 근무일(1)은 출퇴근 시간(7 ~ 9시, 17 ~ 19시)에 대여량이 급증하는 반면,\n"
                "비근무일(0)은 오후(11 ~ 15시) 시간대에 대여량이 상대적으로 높게 나타납니다."
            )

            # by 요일
            st.subheader("요일별 시간대별 평균 대여량")
            fig2, ax2 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='dayofweek', data=df, ax=ax2)
            ax2.set_xlabel("Hour");
            ax2.set_ylabel("Average Count")
            st.pyplot(fig2)
            st.markdown(
                "> **해석:** 평일(월 ~ 금)은 출퇴근 피크가 두드러지고,\n"
                "주말(토~일)은 오전 중반(10 ~ 14시)에 대여량이 더 고르게 분포하는 경향이 있습니다."
            )

            # by 시즌
            st.subheader("시즌별 시간대별 평균 대여량")
            fig3, ax3 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='season', data=df, ax=ax3)
            ax3.set_xlabel("Hour");
            ax3.set_ylabel("Average Count")
            st.pyplot(fig3)
            st.markdown(
                "> **해석:** 여름(2)과 가을(3)에 전반적으로 대여량이 높고,\n"
                "겨울(4)은 전 시간대에 걸쳐 대여량이 낮게 나타납니다."
            )

            # by 날씨
            st.subheader("날씨 상태별 시간대별 평균 대여량")
            fig4, ax4 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='weather', data=df, ax=ax4)
            ax4.set_xlabel("Hour");
            ax4.set_ylabel("Average Count")
            st.pyplot(fig4)
            st.markdown(
                "> **해석:** 맑음(1)은 전 시간대에서 대여량이 가장 높으며,\n"
                "안개·흐림(2), 가벼운 비/눈(3)에선 다소 감소하고, 심한 기상(4)에서는 크게 떨어집니다."
            )


            # 변환 전·후 분포 비교
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))

            # 원본 분포
            sns.histplot(df['count'], kde=True, ax=axes[0])
            axes[0].set_title("Original Count Distribution")
            axes[0].set_xlabel("Count")
            axes[0].set_ylabel("Frequency")

            # 로그 변환 분포
            df['log_count'] = np.log1p(df['count'])
            sns.histplot(df['log_count'], kde=True, ax=axes[1])
            axes[1].set_title("Log(Count + 1) Distribution")
            axes[1].set_xlabel("Log(Count + 1)")
            axes[1].set_ylabel("Frequency")

            st.pyplot(fig)

            st.markdown("""
                > **그래프 해석:**  
                > - 왼쪽: 원본 분포는 한쪽으로 긴 꼬리를 가진 왜곡된 형태입니다.  
                > - 오른쪽: 로그 변환 후 분포는 훨씬 균형잡힌 형태로, 중앙값 부근에 데이터가 집중됩니다.  
                > - 극단치의 영향이 완화되어 이후 분석·모델링 안정성이 높아집니다.
                """)




# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()