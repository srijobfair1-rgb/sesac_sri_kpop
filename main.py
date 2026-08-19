import os
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_saramin_jobs_by_jobcd(group_name, job_cd_string, api_key):
    url = "https://oapi.saramin.co.kr/job-search"
    headers = {"Accept": "application/json"}
    
    params = {
        "access-key": api_key,
        "job_cd": job_cd_string,  # 직무코드 (예: "84,86,87")
        "sort": "pd",             # 최신순
        "count": "110"            # 최대 수집 개수
    }
    
    jobs = []
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            job_list = data.get("jobs", {}).get("job", [])
            
            if isinstance(job_list, dict):
                job_list = [job_list]
                
            today_str = datetime.now().strftime("%Y-%m-%d")
            yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                
            for item in job_list:
                post_time = item.get("posting-timestamp", "")
                if post_time:
                    post_date = datetime.fromtimestamp(int(post_time)).strftime("%Y-%m-%d")
                else:
                    post_date = today_str 
                
                # 어제 ~ 오늘 등록된 공고만 수집
                if post_date in [today_str, yesterday_str]:
                    corp_name = item.get("company", {}).get("detail", {}).get("name", "기업명 미상")
                    title = item.get("position", {}).get("title", "제목 없음")
                    link = item.get("url", "")
                    display_date = datetime.fromtimestamp(int(post_time)).strftime("%m/%d") if post_time else "최신"
                    
                    jobs.append({
                        "corp": corp_name,
                        "title": title,
                        "link": link,
                        "date": display_date
                    })
    except Exception as e:
        print(f"[{group_name}] API 에러: {e}")
        
    return jobs

def send_email(jobs_results):
    sender_email = "sri.jobfair1@gmail.com"
    receiver_email = "sesac@saramin.co.kr"
    password = os.environ.get("GMAIL_APP_PW")
    
    if not password:
        print("🚨 지메일 비밀번호가 세팅되지 않았습니다.")
        return

    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y년 %m월 %d일")
    
    msg = MIMEMultipart()
    msg["Subject"] = f"[RPA] {date_str} 사람인 맞춤 직무 신규 채용공고"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    
    total_count = sum(len(jobs) for jobs in jobs_results.values())
    
    if total_count == 0:
        body = f"{date_str} 기준, 설정하신 직무에 등록된 신규 공고가 없습니다."
    else:
        body = f"총 {total_count}건의 맞춤 직무 공고가 수집되었습니다. (어제~오늘 등록분)\n\n"
        for group_name, jobs in jobs_results.items():
            body += f"📌 [{group_name}] 신규 공고 ({len(jobs)}건)\n"
            body += "-" * 50 + "\n"
            if not jobs:
                body += "해당 직무의 신규 공고가 없습니다.\n\n"
            else:
                for i, job in enumerate(jobs, 1):
                    body += f"{i}. {job['corp']} | {job['title']} ({job['date']})\n   👉 링크: {job['link']}\n"
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
        # 💡 직무 그룹 설정 (코드표 참고해서 원하는 숫자를 넣으세요!)
        job_groups = [
            {"name": "K-POP", "job_cd": "1370,1333,1345,1281"}
        ]
        
        jobs_results = {}
        print("🚀 사람인 API 크롤링 시작...")
        for group in job_groups:
            jobs = get_saramin_jobs_by_jobcd(group["name"], group["job_cd"], api_key)
            jobs_results[group["name"]] = jobs
            print(f"[{group['name']}] {len(jobs)}건 수집 완료")
            
        send_email(jobs_results)
