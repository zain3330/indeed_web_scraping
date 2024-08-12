import time
import re
import csv
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def init():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(options=chrome_options)


def crawlPage(driver, url):
    driver.get(url)
    driver.implicitly_wait(10)
    driver.execute_script("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")
    time.sleep(3)
    return driver.page_source


def parseHtml(html):
    return BeautifulSoup(html, "html.parser")


def findSection(soup):
    jobsSection = soup.find("ul", class_="css-zu9cdh eu4oa1w0")
    print("Total Containers: " + str(len(jobsSection)))
    return jobsSection


def findJobs(jobsSection):
    return jobsSection.find_all("li", class_="css-5lfssm eu4oa1w0")



def extract_job_details(job):
    try:
        jobCard = job.find("div", class_="job_seen_beacon")
        jobHeader = jobCard.find("table", class_="big6_visualChanges css-1v79ar eu4oa1w0")
        tbody = jobHeader.find("tbody")
        jobFooter = jobCard.find("div", class_="heading6 tapItem-gutter css-1rgici5 eu4oa1w0")
        jobDesSection = jobFooter.find("div", class_="css-9446fg eu4oa1w0")
        jobDes = jobDesSection.text.split("\n")
        jobDes = [line.strip() for line in jobDes if line.strip()]
        jobPostedTime = jobFooter.find("span", {"data-testid": "myJobsStateDate"}).text.strip()
        jobLocation = jobHeader.find("div", class_="company_location css-17fky0v e37uo190")
        companyName = jobLocation.find("span", {"data-testid": "company-name"}).text.strip()
        companyLocation = jobHeader.find("div", {"data-testid": "text-location"}).text.strip()
        jobTitleElement = tbody.find("h2", class_="jobTitle css-198pbd eu4oa1w0")
        jobTitle = jobTitleElement.find("span").text.strip()
        jobTypeSalarySection = tbody.find("div", class_="jobMetaDataGroup css-pj786l eu4oa1w0") if tbody else None
        jobSalaryElement = jobTypeSalarySection.find("div", class_="metadata salary-snippet-container css-5zy3wz eu4oa1w0") if jobTypeSalarySection else None
        jobSalary = jobSalaryElement.text.strip() if jobSalaryElement else None
        jobTypeElement = jobTypeSalarySection.find("div", class_="metadata css-5zy3wz eu4oa1w0") if jobTypeSalarySection else None
        jobType = jobTypeElement.find("div", {"data-testid": "attribute_snippet_testid"}).text.strip() if jobTypeElement else None

        return {
            "title": jobTitle,
            "companyName": companyName,
            "companyLocation": companyLocation,
            "jobSalary": jobSalary,
            "type": jobType,
            "dec": jobDes,
            "posted": jobPostedTime,
        }

    except AttributeError:
        return None



def get_next_page_url(soup):
    next_button = soup.find("a", {"aria-label": "Next Page"})
    if next_button:
        return "https://pk.indeed.com" + next_button['href']
    return None


def scrape_all_pages(driver, start_url):
    csvData = []
    url = start_url

    while url:
        html = crawlPage(driver, url)
        soup = parseHtml(html)
        jobsSection = findSection(soup)
        jobs = findJobs(jobsSection)

        for job in jobs:
            jobDetails = extract_job_details(job)
            if jobDetails:
                csvData.append(jobDetails)

        url = get_next_page_url(soup)
        print("Moving to next page...")

    return csvData


driver = init()
start_url = "https://pk.indeed.com/jobs?q=computer+operator&l=Lahore&from=searchOnDesktopSerp&vjk=4389f65a1bb8db81"
csvData = scrape_all_pages(driver, start_url)
driver.quit()

with open("indeed-jobs.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Title", "Company Name", "Company Location", "Salary", "Type", "Dec", "Posted"])
    for job in csvData:
        writer.writerow([
            job['title'],
            job['companyName'],
            job['companyLocation'],
            job['jobSalary'],
            job['type'],
            job['dec'],
            job['posted']
        ])

with open("indeed-jobs.json", "w") as json_file:
    json.dump(csvData, json_file, indent=4)
