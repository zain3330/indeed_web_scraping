import time
import re
import csv
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from db_connection import connect_to_database


def init():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Add additional headers if needed
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(options=chrome_options)


def crawlPage(driver):
    # Send a GET request to the website
    url = "https://pk.indeed.com/jobs?q=web+developer&l=Lahore&from=searchOnDesktopSerp&vjk=2cda8a8041e1816b"
    driver.get(url)

    # Wait for the JavaScript content to load
    driver.implicitly_wait(10)

    # Scroll to the bottom of the page to load all the content
    driver.execute_script("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")

    # Wait for 5 seconds to allow content to load
    time.sleep(3)

    # Get the HTML content of the page
    return driver.page_source


def parseHtml(html):
    # Create a BeautifulSoup object to parse the HTML content
    return BeautifulSoup(html, "html.parser")


def findSection(soup):
    # Find section for job
    jobsSection = soup.find("ul", class_="css-zu9cdh eu4oa1w0")
    # job section
    print("Total Containers: " + str(len(jobsSection)))
    return jobsSection



def findJobs(jobsSection):
    # finad all jobs in section
    return jobsSection.find_all("li", class_="css-5lfssm eu4oa1w0")


def extract_job_details(job):
    try:
        # job card
        jobCard = job.find("div", class_="job_seen_beacon")
        # job header
        jobHeader = jobCard.find("table", class_="big6_visualChanges css-1v79ar eu4oa1w0")
        # job body
        tbody = jobHeader.find("tbody")
        # job footer
        jobFooter =jobCard.find("div" ,class_="heading6 tapItem-gutter css-1rgici5 eu4oa1w0")
        # job des section
        jobDesSection =jobFooter.find("div", class_="css-9446fg eu4oa1w0")
        # job des
        jobDes = jobDesSection.text.split("\n")
        jobDes = [line.strip() for line in jobDes if line.strip()]
        #  job posted  time
        jobPostedTime =jobFooter.find("span" , {"data-testid": "myJobsStateDate"})
        # job posted time text
        jobPostedTimeText =jobPostedTime.text.strip()
        # print("========================")
        # print(jobPostedTimeText)
        #  job location
        jobLocation = jobHeader.find("div", class_="company_location css-17fky0v e37uo190")
        # company name
        companyName = jobLocation.find("span",{"data-testid":"company-name"}).text.strip()
        # company location
        companyLocation = jobHeader.find("div",{"data-testid":"text-location"}).text.strip()
        # title element
        jobTitleElement = tbody.find("h2", class_="jobTitle css-198pbd eu4oa1w0")
        # title span
        jobTitleSpan = jobTitleElement.find("span")
        # title
        jobTitle = jobTitleSpan.text.strip()
        # company name
        jobCompany = tbody.find("div", class_="company_location css-17fky0v e37uo190").text.strip()

        # job and salary section
        jobTypeSalarySection =tbody.find("div" ,class_="jobMetaDataGroup css-pj786l eu4oa1w0")  if tbody else None

        # find job salary
        jobSalaryElement =jobTypeSalarySection.find("div" ,class_="metadata salary-snippet-container css-5zy3wz eu4oa1w0")
        jobSalary = jobSalaryElement.text.strip() if jobSalaryElement else None

        # find job type
        jobTypeElement = jobTypeSalarySection.find("div", class_="metadata css-5zy3wz eu4oa1w0")
        jobType = jobTypeElement.find("div", {"data-testid": "attribute_snippet_testid"}).text.strip() if jobTypeElement else None

        #job detail
        # jobClickUrl =jobTitleElement.find("a", class_="jcs-JobTitle css-jspxzf eu4oa1w0").get("href")
        # print(jobClickUrl)

        return {
            "title": jobTitle,
            # "company": jobCompany,
            "companyName": companyName,
            "companyLocation": companyLocation,
            "jobSalary": jobSalary,
            "type": jobType,
            "dec": ' '.join(jobDes),
            "posted": jobPostedTimeText,
        }

    except AttributeError as e:
        return None





driver = init()
html = crawlPage(driver)
soup = parseHtml(html)

# Find the section containing job listings
jobsSection = findSection(soup)
# Find all job listings
jobs = findJobs(jobsSection)

csvData = []
for job in jobs:
    jobDetails = extract_job_details(job)
    if jobDetails:
        # print("==============================================")
        # print(jobDetails)
        csvData.append(jobDetails)
driver.quit()


with open("indeed-jobs.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Title","Company Name","Company Location","Salary","Type","Dec","Posted"])
    for job in csvData:
        writer.writerow([
            job['title'],
            job['companyName'],
            job['companyLocation'],
            job['jobSalary'],
            job['type'],
            job['dec'],
            job['posted']
        ]
        )
# insert data in mysql
connection = connect_to_database()  # Use your existing connection function
cursor = connection.cursor()
insert_query = '''
        INSERT INTO indeed (title, company_name, company_location, salary, job_type, description, posted_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    '''
for job in csvData:
    cursor.execute(insert_query, (
        job['title'],
        job['companyName'],
        job['companyLocation'],
        job['jobSalary'],
        job['type'],
        job['dec'],
        job['posted']
    ))

connection.commit()
cursor.close()
connection.close()


# Write data to JSON file
with open("indeed-jobs.json", "w") as json_file:
    json.dump(csvData, json_file, indent=4)