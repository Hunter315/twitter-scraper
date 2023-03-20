import json
from tempfile import mkdtemp
import logging
import sys
import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException, NoSuchWindowException

#This part makes logging work locally when testing and in lambda cloud watch
if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


#Function that setup the driver parameters and return driver object.
def open_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = '/opt/chrome/chrome'
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-client-side-phishing-detection')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--lang=en')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")
    chrome = webdriver.Chrome("/opt/chromedriver", options=options)

    return chrome

def save_to_dynamo(handle, url):
    dynamodb = boto3.client('dynamodb', region_name='us-west-2')
    table_name = 'twitter-profile-photos'
    response = dynamodb.put_item(
        TableName=table_name,
        Item={ 
            'handle': {"S": handle},
            'url': {"S": url}
        }
    )
    return response
    

def lambda_handler(event, context):
    body_string = event['body']
    body = json.loads(body_string)
    handle = body['handle']
    logging.info(f"processing handle : {handle}")
    url = f'https://twitter.com/{handle}'   
    try:

        # Open driver
        logging.info("Open Driver")
        driver = open_driver()

        # Clean cookies
        driver.delete_all_cookies()
        driver.set_page_load_timeout(60)

        # Open web
        # logging.info("Opening web " + os.environ['URL'])
        driver.get(url)

        # grab profile photo miniature from profile
        target_XPATH = '//img[@class="css-9pa8cd"]'
        target = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, target_XPATH)))
        photo_url = target.get_attribute('src')
        print(photo_url)
        logging.info(photo_url)
        
        save_to_dynamo(handle, photo_url)
        
        # If we want a full size photo, there a few options to getting it. Right now, we are capturing the 200x200 version.
        # We can either click into the picture again to get the whole version, or just remove the final '_200x200' out of the photo_url
        #driver.close() might not be required since the container is destroyed anyway after done.
        driver.close()
        return  {
        "statusCode": 200,
        "body": photo_url,
    }

    except AssertionError as msg:
        logging.error(msg)
        driver.close()
        sys.exit()
    except TimeoutException:
        logging.error('Request Time Out')
        driver.close()
        sys.exit()
    except WebDriverException:
        logging.error('------------------------ WebDriver-Error! ---------------------', exc_info=True)
        logging.error('------------------------ WebDriver-Error! END ----------------')
        driver.close()
        sys.exit()
    except NoSuchWindowException:
        logging.error('Window is gone, somehow...- NoSuchWindowException')
        sys.exit()
    except NoSuchElementException:
        logging.error('------------------------ No such element on site. ------------------------', exc_info=True)
        logging.error('------------------------ No such element on site. END ------------------------')
        driver.close()
        sys.exit()
