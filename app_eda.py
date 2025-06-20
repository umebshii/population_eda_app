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
                **인구 통계 데이터셋**  
                - 제공처: [통계청 KOSIS](https://kosis.kr)  
                - 설명: 전국 및 시도별 연도별 인구, 출생아수, 사망자수 등의 주요 인구 지표를 포함한 통계 데이터  
                - 데이터 범위: 약 2000년대 초반부터 2022년까지  
                - 주요 변수:  
                  - `연도 (year)`: 기준 연도  
                  - `지역 (region)`: 전국 또는 시도 단위 지역  
                  - `인구 (population)`: 해당 연도 및 지역의 총인구 수  
                  - `출생아수(명) (births)`: 해당 연도의 출생자 수  
                  - `사망자수(명) (deaths)`: 해당 연도의 사망자 수  
                - 활용 목적:  
                  - 연도별/지역별 인구 추이 시각화  
                  - 출생아수 및 사망자수 기반 인구 변화 분석  
                  - 향후 인구 추세 예측 및 정책적 시사점 도출
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

        df = pd.read_csv(uploaded)

        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

        # 1. 기초 통계
        with tabs[0]:
            # ‘세종’ 지역 결측치 '-' → 0 치환
            mask_sejong = df['지역'] == '세종'
            df.loc[mask_sejong, :] = df.loc[mask_sejong, :].replace('-', 0)

            # 숫자 변환
            cols_to_numeric = ['인구', '출생아수(명)', '사망자수(명)']
            for col in cols_to_numeric:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # df.info() 출력
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            # df.describe() 출력
            st.dataframe(df.describe())

        # 2. 연도별 추이
        with tabs[1]:
            # '전국' 필터링
            nation_df = df[df['지역'] == '전국'].copy()

            # 연도별 인구 데이터
            pop_year = nation_df.groupby('연도')['인구'].sum().reset_index()

            # 최근 3년 데이터 (마지막 3개 연도)
            recent_years = pop_year['연도'].max() - 2
            recent_data = nation_df[nation_df['연도'] >= recent_years]

            # 연도별 출생아수 및 사망자수 합산 (전국 단위)
            birth_death = recent_data.groupby('연도')[['출생아수(명)', '사망자수(명)']].sum().reset_index()

            # 연간 평균 순증가 인구 (출생 - 사망)
            birth_death['net_increase'] = birth_death['출생아수(명)'] - birth_death['사망자수(명)']
            avg_net_increase = birth_death['net_increase'].mean()

            # 2035년까지 예측
            last_year = pop_year['연도'].max()
            last_pop = pop_year[pop_year['연도'] == last_year]['인구'].values[0]

            years_pred = np.arange(last_year+1, 2036)
            predicted_pop = [last_pop + avg_net_increase * (year - last_year) for year in years_pred]

            # 그래프 그리기
            plt.figure(figsize=(10,6))
            sns.lineplot(x='연도', y='인구', data=pop_year, marker='o', label='Population')

            # 2035년 예측 추가
            plt.plot(years_pred, predicted_pop, marker='o', linestyle='--', color='red', label='Predicted Population')

            plt.title("Population Trend by Year")
            plt.xlabel("Year")
            plt.ylabel("Population")
            plt.legend()
            plt.grid(True)

            st.pyplot(plt)

        # 3. 지역별 분석
        with tabs[2]:
            # 최근 5년 데이터 필터링 및 전국 제외
            max_year = self.df['연도'].max()
            min_year = max_year - 5
            recent_df = self.df[(self.df['연도'] >= min_year) & (self.df['연도'] <= max_year)]
            recent_df = recent_df[recent_df['지역'] != '전국']

            # 인구 변화량과 변화율 계산
            pop_start = recent_df[recent_df['연도'] == min_year][['지역', '인구']].rename(columns={'인구':'pop_start'})
            pop_end = recent_df[recent_df['연도'] == max_year][['지역', '인구']].rename(columns={'인구':'pop_end'})

            pop_change = pd.merge(pop_start, pop_end, on='지역')
            pop_change['change'] = pop_change['pop_end'] - pop_change['pop_start']
            pop_change['change_rate'] = (pop_change['change'] / pop_change['pop_start']) * 100

            # 한글 지역명 → 영어 매핑 (필요 시 수정)
            region_map = {
                '서울': 'Seoul',
                '부산': 'Busan',
                '대구': 'Daegu',
                '인천': 'Incheon',
                '광주': 'Gwangju',
                '대전': 'Daejeon',
                '울산': 'Ulsan',
                '세종': 'Sejong',
                '경기': 'Gyeonggi',
                '강원': 'Gangwon',
                '충북': 'Chungbuk',
                '충남': 'Chungnam',
                '전북': 'Jeonbuk',
                '전남': 'Jeonnam',
                '경북': 'Gyeongbuk',
                '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            pop_change['region_en'] = pop_change['지역'].map(region_map)

            # 변화량 그래프
            pop_change_sorted = pop_change.sort_values(by='change', ascending=False)
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sns.barplot(data=pop_change_sorted, x=pop_change_sorted['change'] / 1000, y='region_en', palette='viridis', ax=ax1)
            ax1.set_title('Population Change in Last 5 Years (Unit: Thousands)')
            ax1.set_xlabel('Population Change (K)')
            ax1.set_ylabel('Region')
            for i, v in enumerate(pop_change_sorted['change'] / 1000):
                ax1.text(v + 0.5, i, f"{v:.1f}", color='black', va='center')
            st.pyplot(fig1)

            st.markdown("""
            **Explanation:**  
            This chart shows the population change for each region (excluding 'Nationwide') over the last 5 years.  
            Positive values indicate population growth, while negative values indicate a decline. The unit is thousands (K).
            """)

            # 변화율 그래프
            pop_change_rate_sorted = pop_change.sort_values(by='change_rate', ascending=False)
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(data=pop_change_rate_sorted, x='change_rate', y='region_en', palette='magma', ax=ax2)
            ax2.set_title('Population Change Rate in Last 5 Years (%)')
            ax2.set_xlabel('Change Rate (%)')
            ax2.set_ylabel('Region')
            for i, v in enumerate(pop_change_rate_sorted['change_rate']):
                ax2.text(v + 0.2, i, f"{v:.2f}%", color='black', va='center')
            st.pyplot(fig2)

            st.markdown("""
            **Explanation:**  
            This chart shows the percentage population change over the last 5 years by region.  
            It provides a relative measure of growth or decline compared to the population 5 years ago.
            """)

        # 4. 변화량 분석
        with tabs[3]:
            # '전국' 제외하고 연도 기준 정렬
            region_df = self.df[self.df['지역'] != '전국'].copy()
            region_df.sort_values(by=['지역', '연도'], inplace=True)

            # 지역별 연도별 인구 증감(diff)
            region_df['증감'] = region_df.groupby('지역')['인구'].diff()

            # 증감 기준 상위 100개 추출 (증가/감소 모두 포함)
            top_diff = region_df.dropna(subset=['증감']).copy()
            top_diff = top_diff.sort_values(by='증감', key=abs, ascending=False).head(100)

            # 천단위 콤마 적용
            top_diff['인구'] = top_diff['인구'].apply(lambda x: f"{int(x):,}")
            top_diff['증감'] = top_diff['증감'].apply(lambda x: f"{int(x):,}")

            # 컬러바 시각화용 Styler 객체 생성
            def color_diff(val):
                val_num = int(val.replace(',', ''))
                color = 'rgba(0, 100, 255, 0.3)' if val_num > 0 else 'rgba(255, 80, 80, 0.3)'
                return f'background-color: {color}'

            styled_df = top_diff[['연도', '지역', '인구', '증감']].style \
                .applymap(color_diff, subset=['증감']) \
                .set_properties(**{'text-align': 'center'}) \
                .set_table_styles([{
                    'selector': 'th',
                    'props': [('text-align', 'center')]
                }])

            st.subheader("💡 Top 100 Population Change Cases by Region (Excl. Nationwide)")
            st.dataframe(styled_df, use_container_width=True)

        # 5. 시각화
        with tabs[4]:
            st.subheader("📊 Stacked Area Chart: Population by Region Over Time")

            # '전국' 제외
            df_local = self.df[self.df['지역'] != '전국'].copy()

            # 연도 오름차순 정렬
            df_local.sort_values(by='연도', inplace=True)

            # 지역명을 영어로 매핑 (예시)
            region_map = {
                "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon",
                "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong",
                "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk", "충남": "Chungnam",
                "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk", "경남": "Gyeongnam",
                "제주": "Jeju"
            }
            df_local['region_en'] = df_local['지역'].map(region_map)

            # 피벗 테이블 생성: 행 = 연도, 열 = 지역, 값 = 인구
            pivot = df_local.pivot_table(index='연도', columns='region_en', values='인구', aggfunc='sum')

            # 누적 영역 그래프 그리기
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot.plot.area(ax=ax, cmap='tab20', alpha=0.8)

            # 축 레이블, 타이틀 설정 (영문)
            ax.set_title("Population Trends by Region (Excl. Nationwide)", fontsize=14)
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, linestyle='--', alpha=0.4)

            st.pyplot(fig)



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