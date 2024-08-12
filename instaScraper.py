from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import sys
import os
import requests
import shutil
from xlsxwriter import Workbook
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

class Scraper:
    def __init__(self, username, password, target_username):
        self.username = username
        self.password = password
        self.target_username = target_username
        self.base_path = os.path.join('data', self.target_username) # change it as per requirement
        self.imagesData_path = os.path.join(self.base_path, 'images') # change it as per requirement 
        self.descriptionsData_path = os.path.join(self.base_path, 'descriptions') # change it as per requirement
        self.driver = webdriver.Chrome() # I'm using linux. You can change it as per your OS.
        self.main_url = 'https://www.instagram.com'
        
        # check the internet connection and if the home page is fully loaded or not. 
        try:
            self.driver.get(self.main_url)
            WebDriverWait(self.driver, 10).until(EC.title_is('Instagram'))
        except TimeoutError:
            print('Loading took too much time. Please check your connection and try again.')
            sys.exit()
        

        self.login()
        # self.close_dialog_box()
        self.open_target_profile()

        # check if the directory to store data exists
        if not os.path.exists('data'):
            os.mkdir('data')
        if not os.path.exists(self.base_path):
            os.mkdir(self.base_path)
        if not os.path.exists(self.imagesData_path):
            os.mkdir(self.imagesData_path)
        if not os.path.exists(self.descriptionsData_path):
            os.mkdir(self.descriptionsData_path)
        self.download_posts()

        self.driver.close()

    def login(self):
        # Navigate to the login page
        login_url = 'https://www.instagram.com/accounts/login/'
        self.driver.get(login_url)

        # Wait for the page to load
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        except TimeoutException:
            print('Loading took too much time. Please check your connection and try again.')
            sys.exit()

        # Locate the username and password fields
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
            username_input = self.driver.find_element(By.NAME, 'username')
        except TimeoutException:
            print('TimeoutException: Unable to find the username field.')
            sys.exit()

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'password'))
            )
            password_input = self.driver.find_element(By.NAME, 'password')
        except TimeoutException:
            print('TimeoutException: Unable to find the password field.')
            sys.exit()

        # Input credentials and submit
        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        password_input.submit()

        # Wait for login to complete
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        except TimeoutException:
            print('Login took too much time, or failed. Please check your credentials or connection and try again.')
            sys.exit()
        print('Waiting 5 seconds...')
        sleep(5)
        print('Login Successful!')

    # def close_dialog_box(self):
    #     ''' Close the Notification Dialog '''
    #     try:
    #         close_btn = self.driver.find_element_by_xpath('//button[text()="Not Now"]')
    #         close_btn.click()
    #     except Exception:
    #         pass 

    def open_target_profile(self):  
        target_profile_url  = self.main_url + '/' + self.target_username
        print('Redirecting to {0} profile...'.format(self.target_username))
        
        # check if the target user profile is loaded. 
        try:
            self.driver.get(target_profile_url) 
            WebDriverWait(self.driver, 3).until(EC.title_contains(self.target_username))
        except TimeoutError:
            print('Some error occurred while trying to load the target username profile.')
            sys.exit()


    def load_fetch_posts(self):
        '''Load and fetch target account posts'''

        image_list = [] # to store the posts

        # get the no of posts
        try:
            no_of_posts_element = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//span[contains(@class, "xdj266r")]'))
            )
            no_of_posts = no_of_posts_element.text.replace(',', '')
            self.no_of_posts = int(no_of_posts)
            print('{0} has {1} posts'.format(self.target_username, self.no_of_posts))
        except Exception as e:
            print('Some exception occurred while trying to find the number of posts:', str(e))
        # try:
        #     no_of_posts = str(self.driver.find_element_by_xpath('//span[@id = "react-root"]//header/section/ul/li//span[@class = "g47SY "]').text).replace(',', '')
        #     self.no_of_posts = int(no_of_posts)
        #     print('{0} has {1} posts'.format(self.target_username, self.no_of_posts))
        # except Exception:
        #     print('Some exception occurred while trying to find the number of posts.')
            sys.exit()

        try:
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            all_images = soup.find_all('img', attrs = {'class': 'FFVAD'})

            for img in all_images:
                if img not in image_list:
                    image_list.append(img)

            if self.no_of_posts > 12: # 12 posts loads up when we open the profile
                no_of_scrolls = round(self.no_of_posts/12) + 6 # extra scrolls if any error occurs while scrolling.
                #no_of_scrolls = 2
                # Loading all the posts
                print('Loading all the posts...')
                for __ in range(no_of_scrolls):

                    # Every time the page scrolls down we need to get the source code as it is dynamic
                    self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                    sleep(3) # introduce sleep time as per your internet connection as to give the time to posts to load

                    soup = BeautifulSoup(self.driver.page_source, 'lxml')
                    all_images = soup.find_all('img')

                    for img in all_images:
                        if img not in image_list:
                            image_list.append(img)


        except Exception as e:
            print('Some error occurred while scrolling down and trying to load all posts:', str(e))
            sys.exit()

        return image_list

    
    def download_descriptions(self, image_list):
        ''' Writing the descriptions in excel file '''
        print('writing the descriptions to excel...')
        workbook = Workbook(os.path.join(self.descriptionsData_path, 'descriptions.xlsx'))
        worksheet = workbook.add_worksheet()
        row = 0
        worksheet.write(row, 0, 'Image name')       # 3 --> row number, column number, value
        worksheet.write(row, 1, 'Description')
        worksheet.write(row, 2, 'URL')
        row += 1
        for index, image in enumerate(image_list, start = 1):
            filename = 'image_' + str(index) + '.jpg'
            try:
                description = image.get('alt')
                url = image.get('src')
            except KeyError:
                description = 'No caption exists'

            if description == '':
                description = 'No caption exists'

            worksheet.write(row, 0, filename)
            worksheet.write(row, 1, description)
            worksheet.write(row, 2, url)
            row += 1
        workbook.close()

    def download_posts(self):
        ''' To download all the posts of the target account '''

        image_list = self.load_fetch_posts()
        self.download_descriptions(image_list)
        no_of_images = len(image_list)
        for index, img in enumerate(image_list, start = 1):
            filename = 'image_' + str(index) + '.jpg'
            image_path = os.path.join(self.imagesData_path, filename)
            link = img.get('src')
            if link.startswith('http'):
                response = requests.get(link, stream = True)
                print('Downloading image {0} of {1}'.format(index, no_of_images))
                try:
                    with open(image_path, 'wb') as file:
                        shutil.copyfileobj(response.raw, file)
                except Exception as e:
                    print(e)
                    print('Couldn\'t download image {0}.'.format(index))
                    print('Link for image {0} ---> {1}'.format(index, link))
        print('Download completed!')