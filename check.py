#!/usr/bin/python3

import base64
import email
import random
import smtplib
import time
import sys 
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from socket import gaierror

from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select

class Mailer():

    def __init__(self, smtp_server, smtp_port, login, password, sender):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.login = login
        self.password = password
        self.sender = sender
        if (len(sender) < 1):
            self.sender = login

    def __str__(self):
        return f"server:   {self.smtp_server}:{self.smtp_port} \nlogin:    {self.login} \npassword: {self.password} \nsender:   {self.sender}"

    def sendMail(self, receiver_email, subject, message):
        print(f"Sending mail from: \n{self}")
        s = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        s.set_debuglevel(1)
        # s.starttls() # to make emails encrypted
        s.login(self.login, self.password)

        msg = MIMEMultipart()

        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = receiver_email

        body = MIMEText(message)
        msg.attach(body)
        s.sendmail(msg["From"], msg["To"].split(","), msg.as_string())
        s.quit()


class Checker():

    def __str__(self):
        return f"receiver: {self.receiver_email} \ntestID: {self.testID}\nbirthday: {self.birthdate_year}-{self.birthdate_month}-{self.birthdate_day}"

    def __init__(self, mailer, receiver_email, testID, birthdate_day, birthdate_month, birthdate_year):
        self.mailer = mailer
        self.receiver_email = receiver_email
        self.testID = testID
        self.birthdate_day = birthdate_day
        self.birthdate_month = birthdate_month
        self.birthdate_year = birthdate_year

        print(self)

        self.check()

    def check(self):
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)

        driver.get("https://www.doctorbox.de/covid19.jsp")
        assert "DoctorBox" in driver.title
        # test ID number
        elem = driver.find_element_by_name("covid19ID")
        elem.clear()
        elem.send_keys(self.testID)
        # birthdate day
        select = Select(driver.find_element_by_name("day"))
        select.select_by_visible_text(self.birthdate_day)
        # birthdate month
        select = Select(driver.find_element_by_name("month"))
        select.select_by_visible_text(self.birthdate_month)
        # birthdate year
        select = Select(driver.find_element_by_name("year"))
        select.select_by_visible_text(self.birthdate_year)

        # Form is filled out! :)
        self.full_screenshot(driver, "covid-form.png")
        self.watermark_time("covid-form.png")

        submit_button = driver.find_element_by_xpath(
            '/html/body/div[3]/section/div/div/div/div/div/div[2]/button')
        submit_button.click()
        driver.save_screenshot("covid-result.png")
        self.watermark_time("covid-result.png")

        try:
            result = driver.find_element_by_xpath(
                "/html/body/div[3]/section/div/div/div[1]/div[2]").text
        except:
            print("FAILED TO GET BIG RESULT TEXT")
            result = ">result text missing<"

        try:
            small_result = driver.find_element_by_xpath(
                "/html/body/div[3]/section/div/div/div[1]/div[2]/h2").text
        except:
            print("FAILED TO GET SMALL RESULT TEXT")
            small_result = ">small_result text missing<"

        # Assumption
        assumption = "unknown"
        if (("positiv" in small_result) and ("negativ" not in small_result)):
            assumption = "positiv"
        if (("positiv" not in small_result) and ("negativ" in small_result)):
            assumption = "negativ"

        if ("noch kein Testergebnis" in result):
            assumption = "not yet"
        else:
            mailer.sendMail(self.receiver_email, "Covid Result " + assumption, result)

        current_time = time.strftime("%d %H:%M:%S", time.localtime())
        print(current_time + "  Assumption: " + assumption)
        driver.close()

    def full_screenshot(self, driver, save_path):
        # initiate value
        save_path = save_path + \
            '.png' if save_path[-4::] != '.png' else save_path
        img_li = []  # to store image fragment
        offset = 0  # where to start

        # js to get height
        height = driver.execute_script('return Math.max('
                                       'document.documentElement.clientHeight, window.innerHeight);')

        # js to get the maximum scroll height
        # Ref--> https://stackoverflow.com/questions/17688595/finding-the-maximum-scroll-position-of-a-page
        max_window_height = driver.execute_script('return Math.max('
                                                  'document.body.scrollHeight, '
                                                  'document.body.offsetHeight, '
                                                  'document.documentElement.clientHeight, '
                                                  'document.documentElement.scrollHeight, '
                                                  'document.documentElement.offsetHeight);')

        # looping from top to bottom, append to img list
        # Ref--> https://gist.github.com/fabtho/13e4a2e7cfbfde671b8fa81bbe9359fb
        while offset < max_window_height:

            # Scroll to height
            driver.execute_script(f'window.scrollTo(0, {offset});')
            img = Image.open(BytesIO((driver.get_screenshot_as_png())))
            img_li.append(img)
            offset += height

        # Stitch image into one
        # Set up the full screen frame
        img_frame_height = sum([img_frag.size[1] for img_frag in img_li])
        img_frame = Image.new('RGB', (img_li[0].size[0], img_frame_height))
        offset = 0
        for img_frag in img_li:
            img_frame.paste(img_frag, (0, offset))
            offset += img_frag.size[1]
        img_frame.save(save_path)

    def watermark_time(self, image_path):
        current_time = time.strftime("%d %H:%M:%S", time.localtime())

        photo = Image.open(image_path)

        # make the image editable
        drawing = ImageDraw.Draw(photo)
        black = (3, 8, 12)
        font = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 40)
        drawing.text((random.randint(140, 470), 46),
                     current_time, fill=black, font=font)
        photo.save(image_path)


def get_configured_mailer():
    arr = open("check.config", "r").read().split("\n")
    return Mailer(arr[0], arr[1],arr[2],arr[3],arr[4])


assert(len(sys.argv) == 6)


mailer = get_configured_mailer()
Checker(mailer, sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
