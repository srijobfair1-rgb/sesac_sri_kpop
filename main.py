import os
import time
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_saramin_jobs(group_name, job_cd_string, loc_cd, exp_cd, api_key):
    url = "https://oapi.saramin.co.kr/job-search"
    headers = {"Accept": "application/json"}
    
    params = {
        "access-key": api_key,
        "job_cd": job_cd_string,  
        "loc_cd": loc_cd,             
        "experience_level": exp_cd,   
        "sort": "pd",                 
        "count": "110"                
    }
    
    jobs_collected = []
    
    # 💡 깃허브 서버 시차 방지: 완벽한 한국 시간 기준 어제 날짜 구하기
    kst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday_str = (kst_now - timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            job_list = data.get("jobs", {}).get("job", [])
            
            # 결과가 1건일 때 리스트로 강제 변환 (오류 방지)
            if isinstance(job_list, dict):
                job_list = [job_list]
                
            for item in job_list:
                post_time = item.get("posting-timestamp")
                if post_time:
                    # 등록 타임스탬프를 한국 시간(KST)으로 변환
                    post_date = (datetime.utcfromtimestamp(int(post_time)) + timedelta(hours=9)).strftime("%Y-%m-%d")
                else:
                    post_date = "" 
                
                # 💡 오직 '어제' 등록된 공고만 필터링!
                if post_date == yesterday_str:
                    corp_name = item.get("company", {}).get("detail", {}).get("name", "기업명 미상")
                    title = item.get("position", {}).get("title", "제목 없음")
                    link = item.get("url", "")
                    
                    exp_text = item.get("position", {}).get("experience-level", {}).get("name", "")
                    loc_text = item.get("position", {}).get("location", {}).get("name-kr", "")
                    
                    open_time = item.get("opening-timestamp")
                    close_time = item.get("expiration-timestamp")
                    
                    open_date = (datetime.utcfromtimestamp(int(open_time)) + timedelta(hours=9)).strftime("%Y-%m-%d") if open_time else "-"
                    close_date = (datetime.utcfromtimestamp(int(close_time)) + timedelta(hours=9)).strftime("%Y-%m-%d") if close_time else "상시채용/채용시 마감"
                    
                    jobs_collected.append({
                        "corp": corp_name,
                        "title": f"[{exp_text}/{loc_text}] {title}",
                        "link": link,
                        "open_date": open_date,
                        "close_date": close_date
                    })
    except Exception as e:
        print(f"[{group_name}] API 통신 에러: {e}")
        
    return jobs_collected

def send_email(jobs_results, receiver_emails, target_tag):
    sender_email = "sri.jobfair1@gmail.com"
    password = os.environ.get("GMAIL_APP_PW")
    
    if not password:
        print("🚨 GMAIL_APP_PW 비밀번호가 없습니다.")
        return

    # 메일 제목용 어제 날짜 (KST 기준)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday_str = (kst_now - timedelta(days=1)).strftime("%Y년 %m월 %d일")
    
    msg = MIMEMultipart()
    msg["Subject"] = f"[{target_tag}] {yesterday_str} 신규 채용공고 리포트"
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
    
    total_count = sum(len(jobs) for jobs in jobs_results.values())
    
    if total_count == 0:
        body = f"{yesterday_str}에 등록된 [{target_tag}] 맞춤 신규 공고가 없습니다."
    else:
        body = f"[{target_tag}] 총 {total_count}건의 맞춤 공고가 수집되었습니다. (전일 등록분)\n\n"
        for group_name, jobs in jobs_results.items():
            body += f"📌 [{group_name}] 전일 등록 공고 ({len(jobs)}건)\n"
            body += "-" * 50 + "\n"
            if not jobs:
                body += "해당 직무에 전일 등록된 공고가 없습니다.\n\n"
            else:
                for i, job in enumerate(jobs, 1):
                    body += f"{i}. {job['corp']} | {job['title']}\n"
                    body += f"   📅 접수기간: {job['open_date']} ~ {job['close_date']}\n"
                    body += f"   👉 링크: {job['link']}\n\n"
            body += "\n"
            
    msg.attach(MIMEText(body, "plain"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        print(f"✅ [{target_tag}] 메일 발송 완료! -> {', '.join(receiver_emails)}")
    except Exception as e:
        print(f"❌ [{target_tag}] 메일 발송 실패: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("SARAMIN_API_KEY")
    
    if not api_key:
        print("🚨 SARAMIN_API_KEY가 없습니다.")
    else:
        # ======================================================
        # 💡 설정 영역 (서울 101000 / 신입 단독 1)
        # ======================================================
        TARGET_LOC_CD = "101000"
        TARGET_EXP_CD = "1"
        
        # 각 부서(메일함)별로 수집할 직무와 수신자를 독립적으로 지정합니다.
        # 코드가 절대 꼬이지 않도록 배열(List) 구조를 가장 직관적으로 분리했습니다.
        email_targets = [
            {
                "tag": "케이랩컴퍼니 'K-Pop'",
                "receivers": ["sesac@saramin.co.kr"], # 👈 실제 받으실 첫 번째 메일 주소
                "job_groups": [
                     {"name": "K-POP", "job_cd": "1370,1333,1389"}
                ]
            },
             {
                "tag": "양천캠퍼스'",
                "receivers": ["sesac@saramin.co.kr"], # 👈 실제 받으실 첫 번째 메일 주소
                "job_groups": [
                     {"name": "마케팅/MD", "job_cd": "1429,1435,2201,2245,2237"}
                ]
            }
        ]
        
        print("🚀 [RPA 크롤러 시작] 그룹별 개별 수집 및 발송 진행...\n")
        
        for target in email_targets:
            tag = target["tag"]
            receivers = target["receivers"]
            groups = target["job_groups"]
            
            print(f"=====================================")
            print(f"📌 타겟: [{tag}] 작업을 시작합니다.")
            print(f"=====================================")
            
            jobs_results = {}
            for group in groups:
                group_name = group["name"]
                job_cd = group["job_cd"]
                
                # API로 공고 가져오기
                jobs = get_saramin_jobs(group_name, job_cd, TARGET_LOC_CD, TARGET_EXP_CD, api_key)
                jobs_results[group_name] = jobs
                print(f"  └ {group_name}: {len(jobs)}건 수집 완료")
                
                # 💡 API 호출 간격 1초 대기 (서버 차단 방지)
                time.sleep(1) 
                
            # 해당 타겟에게 메일 발송
            send_email(jobs_results, receivers, tag)
            
            # 💡 [중요] 메일을 연속으로 보내면 지메일 스팸 차단이 발생할 수 있어 3초 대기합니다.
            time.sleep(3) 
            print("\n")


