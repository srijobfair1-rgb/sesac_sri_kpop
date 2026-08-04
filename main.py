import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time
from datetime import datetime, timedelta

def get_saramin_jobs_mobile(keyword):
    # 💡 모바일 사람인 검색 (sort=pd : 최신 등록일순 정렬)
    url = f"https://m.saramin.co.kr/job-search?searchword={keyword}&sort=pd"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }
    
    jobs = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 모바일 사람인 공고 카드 구조 가져오기 (다양한 모바일 클래스 대응)
        recruit_items = soup.select('.list_recruiting .item_recruit, .recruitment_list .item_recruit, .area_job, .list_item')
        
        # 태그를 못 찾았을 경우 대비한 2차 검색
        if not recruit_items:
            recruit_items = soup.find_all('div', class_=lambda c: c and 'item_recruit' in c)
            
        print(f"👉 [{keyword}] 검색 결과 페이지에서 공고 카드 {len(recruit_items)}개를 감지했습니다.")
        
        for item in recruit_items:
            try:
                # 1. 회사명
                corp_elem = item.select_one('.corp_name, .company_name, .corp')
                corp_name = corp_elem.text.strip() if corp_elem else "기업명 미상"
                
                # 2. 공고 제목
                title_elem = item.select_one('.job_tit, .tit, .title_link')
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # 3. 공고 링크
                link_elem = item.select_one('a')
                if link_elem and 'href' in link_elem.attrs:
                    link = "https://m.saramin.co.kr" + link_elem['href']
                else:
                    link = "https://m.saramin.co.kr"
                
                # 4. 날짜/뱃지 정보
                date_badge = item.select_one('.badge_date, .job_day, .date, .time')
                date_text = date_badge.text.strip() if date_badge else ""
                
                # 등록일순(sort=pd)으로 가져왔으므로 최신 공고 리스트에 담습니다.
                jobs.append({
                    'corp': corp_name,
                    'title': title,
                    'link': link,
                    'date': date_text
                })
                
                # 상위 15개 최신 공고만 수집 (너무 많아지는 것 방지)
                if len(jobs) >= 15:
                    break
                    
            except Exception:
                continue
                
    except Exception as e:
        print(f"'{keyword}' 크롤링 중 오류 발생: {e}")
        
    return jobs

def send_email(jobs_by_keyword):
    sender_email = "sri.jobfair1@gmail.com"
    receiver_email = "sesac@saramin.co.kr"
    password = os.environ.get('GMAIL_APP_PW') 
    
    if not password:
        print("이메일 앱 비밀번호가 설정되지 않았습니다.")
        return

    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y년 %m월 %d일')
    keyword_str = ", ".join(jobs_by_keyword.keys())
    
    msg = MIMEMultipart()
    msg['Subject'] = f"[RPA] {date_str} 사람인 '{keyword_str}' 최신 채용공고"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    total_count = sum(len(jobs) for jobs in jobs_by_keyword.values())
    
    if total_count == 0:
        body = f"{date_str} 기준, 수집된 신규 공고가 없습니다."
    else:
        body = f"총 {total_count}건의 최신 공고가 수집되었습니다. (등록일순 정렬)\n\n"
        for keyword, jobs in jobs_by_keyword.items():
            body += f"📌 [{keyword}] 검색 결과 ({len(jobs)}건)\n"
            body += "-" * 40 + "\n"
            if len(jobs) == 0:
                body += "검색된 공고가 없습니다.\n\n"
            else:
                for i, job in enumerate(jobs, 1):
                    date_info = f" ({job['date']})" if job['date'] else ""
                    body += f"{i}. {job['corp']} | {job['title']}{date_info}\n   👉 링크: {job['link']}\n"
            body += "\n"
            
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        print("메일 발송 성공!")
    except Exception as e:
        print(f"메일 발송 실패: {e}")

if __name__ == "__main__":
    keywords = ["공연", "엔터테인먼트"]
    jobs_by_keyword = {}
    
    for keyword in keywords:
        print(f"'{keyword}' 수집 시작...")
        jobs = get_saramin_jobs_mobile(keyword)
        jobs_by_keyword[keyword] = jobs
        print(f"'{keyword}' 수집 완료: {len(jobs)}건")
        time.sleep(2)
        
    print("메일 발송을 시작합니다...")
    send_email(jobs_by_keyword)
