import os
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_saramin_jobs_by_jobcd(group_name, job_cd_string, loc_cd, exp_cd, api_key):
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
    
    jobs = []
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            job_list = data.get("jobs", {}).get("job", [])
            
            if isinstance(job_list, dict):
                job_list = [job_list]
                
            kst_now = datetime.utcnow() + timedelta(hours=9)
            yesterday_str = (kst_now - timedelta(days=1)).strftime("%Y-%m-%d")
                
            for item in job_list:
                post_time = item.get("posting-timestamp", "")
                if post_time:
                    # 등록 타임스탬프도 한국 시간 기준으로 날짜 변환
                    post_date = (datetime.utcfromtimestamp(int(post_time)) + timedelta(hours=9)).strftime("%Y-%m-%d")
                else:
                    post_date = "" 
                
                if post_date == yesterday_str:
                    corp_name = item.get("company", {}).get("detail", {}).get("name", "기업명 미상")
                    title = item.get("position", {}).get("title", "제목 없음")
                    link = item.get("url", "")
                    
                    exp_text = item.get("position", {}).get("experience-level", {}).get("name", "")
                    loc_text = item.get("position", {}).get("location", {}).get("name-kr", "")
                    
                    open_time = item.get("opening-timestamp", "")
                    close_time = item.get("expiration-timestamp", "")
                    
                    open_date = (datetime.utcfromtimestamp(int(open_time)) + timedelta(hours=9)).strftime("%Y-%m-%d") if open_time else "-"
                    close_date = (datetime.utcfromtimestamp(int(close_time)) + timedelta(hours=9)).strftime("%Y-%m-%d") if close_time else "상시채용/채용시 마감"
                    
                    jobs.append({
                        "corp": corp_name,
                        "title": f"[{exp_text}/{loc_text}] {title}",
                        "link": link,
                        "open_date": open_date,
                        "close_date": close_date
                    })
    except Exception as e:
        print(f"[{group_name}] API 에러: {e}")
        
    return jobs

def send_email(jobs_results, receiver_emails):
    sender_email = "sri.jobfair1@gmail.com"
    password = os.environ.get("GMAIL_APP_PW")
    
    if not password:
        print("🚨 지메일 비밀번호가 세팅되지 않았습니다.")
        return

    # 메일 제목에도 한국 시간 기준 어제 날짜를 박아줍니다.
    kst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday = kst_now - timedelta(days=1)
    date_str = yesterday.strftime("%Y년 %m월 %d일")
    
    msg = MIMEMultipart()
    msg["Subject"] = f"[RPA] {date_str} 등록분 사람인 서울/신입 채용공고"
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
    
    total_count = sum(len(jobs) for jobs in jobs_results.values())
    
    if total_count == 0:
        body = f"{date_str}에 등록된 조건(서울/신입)의 신규 공고가 없습니다."
    else:
        body = f"총 {total_count}건의 공고가 수집되었습니다. (전일 00:00~23:59 등록분)\n\n"
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
        print("✅ 메일 발송 성공!")
    except Exception as e:
        print(f"❌ 메일 발송 실패: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("SARAMIN_API_KEY")
    
    if not api_key:
        print("🚨 오류: SARAMIN_API_KEY가 등록되지 않았습니다.")
    else:
        RECEIVER_EMAILS = [
            "sesac@saramin.co.kr"
        ]
        
        TARGET_LOC_CD = "101000"  # 서울 전체
        TARGET_EXP_CD = "1"       # 신입
        
        job_groups = [
            {"name": "K-POP", "job_cd": "1370,1333,1345,1281"}
        ]
        
        jobs_results = {}
        print("🚀 사람인 API 크롤링 시작...")
        for group in job_groups:
            jobs = get_saramin_jobs_by_jobcd(group["name"], group["job_cd"], TARGET_LOC_CD, TARGET_EXP_CD, api_key)
            jobs_results[group["name"]] = jobs
            print(f"[{group['name']}] {len(jobs)}건 수집 완료")
            
        send_email(jobs_results, RECEIVER_EMAILS)



import os
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_saramin_jobs_by_jobcd(group_name, job_cd_string, loc_cd, exp_cd, api_key):
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
    
    jobs = []
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            job_list = data.get("jobs", {}).get("job", [])
            
            if isinstance(job_list, dict):
                job_list = [job_list]
                
            kst_now = datetime.utcnow() + timedelta(hours=9)
            yesterday_str = (kst_now - timedelta(days=1)).strftime("%Y-%m-%d")
                
            for item in job_list:
                post_time = item.get("posting-timestamp", "")
                if post_time:
                    post_date = (datetime.utcfromtimestamp(int(post_time)) + timedelta(hours=9)).strftime("%Y-%m-%d")
                else:
                    post_date = "" 
                
                # 전일 등록분만 필터링
                if post_date == yesterday_str:
                    corp_name = item.get("company", {}).get("detail", {}).get("name", "기업명 미상")
                    title = item.get("position", {}).get("title", "제목 없음")
                    link = item.get("url", "")
                    
                    exp_text = item.get("position", {}).get("experience-level", {}).get("name", "")
                    loc_text = item.get("position", {}).get("location", {}).get("name-kr", "")
                    
                    open_time = item.get("opening-timestamp", "")
                    close_time = item.get("expiration-timestamp", "")
                    
                    open_date = (datetime.utcfromtimestamp(int(open_time)) + timedelta(hours=9)).strftime("%Y-%m-%d") if open_time else "-"
                    close_date = (datetime.utcfromtimestamp(int(close_time)) + timedelta(hours=9)).strftime("%Y-%m-%d") if close_time else "상시채용/채용시 마감"
                    
                    jobs.append({
                        "corp": corp_name,
                        "title": f"[{exp_text}/{loc_text}] {title}",
                        "link": link,
                        "open_date": open_date,
                        "close_date": close_date
                    })
    except Exception as e:
        print(f"[{group_name}] API 에러: {e}")
        
    return jobs

def send_email(jobs_results, receiver_emails, target_tag):
    sender_email = "sri.jobfair1@gmail.com"
    password = os.environ.get("GMAIL_APP_PW")
    
    if not password:
        print("🚨 지메일 비밀번호가 세팅되지 않았습니다.")
        return

    kst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday = kst_now - timedelta(days=1)
    date_str = yesterday.strftime("%Y년 %m월 %d일")
    
    msg = MIMEMultipart()
    # 💡 제목에 타겟 태그(예: [개발팀], [마케팅팀])를 동적으로 추가
    msg["Subject"] = f"[RPA-{target_tag}] {date_str} 사람인 신규 채용공고"
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
    
    total_count = sum(len(jobs) for jobs in jobs_results.values())
    
    if total_count == 0:
        body = f"{date_str}에 등록된 [{target_tag}] 맞춤 신규 공고가 없습니다."
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
        print(f"✅ [{target_tag}] 메일 발송 성공! -> {', '.join(receiver_emails)}")
    except Exception as e:
        print(f"❌ [{target_tag}] 메일 발송 실패: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("SARAMIN_API_KEY")
    
    if not api_key:
        print("🚨 오류: SARAMIN_API_KEY가 등록되지 않았습니다.")
    else:
        TARGET_LOC_CD = "101000"  # 서울 전체
        TARGET_EXP_CD = "1"       # 신입
        
        # =====================================================================
        # 💡 [핵심] 수신 타겟별로 메일주소와 직무 그룹을 각각 설정합니다.
        # 원하는 만큼 { ... } 블록을 늘려주기만 하면 됩니다.
        # =====================================================================
        email_targets = [
            {
                "tag": "K-POP",
                "receivers": ["sesac@saramin.co.kr"],
                "job_groups": [
                {"name": "K-POP", "job_cd": "1370,1333,1345,1281"}
                ]
            },
            
            # 💡 필요시 타겟 추가 예시:
            # {
            #     "tag": "디자인팀",
            #     "receivers": ["design@saramin.co.kr"],
            #     "job_groups": [
            #         {"name": "디자인 전체", "job_cd": "16"}
            #     ]
            # }
        ]
        
        print("🚀 그룹별 맞춤 사람인 API 크롤링 및 발송 시작...\n")
        
        # 설정된 타겟 수만큼 반복 실행
        for target in email_targets:
            tag = target["tag"]
            receivers = target["receivers"]
            groups = target["job_groups"]
            
            print(f"📌 [{tag}] 작업 진행 중...")
            jobs_results = {}
            
            for group in groups:
                jobs = get_saramin_jobs_by_jobcd(group["name"], group["job_cd"], TARGET_LOC_CD, TARGET_EXP_CD, api_key)
                jobs_results[group["name"]] = jobs
                print(f"  - {group['name']}: {len(jobs)}건 수집")
                
            send_email(jobs_results, receivers, tag)
            print("-" * 40)
