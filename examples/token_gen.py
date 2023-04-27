import sys
import poe
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

# Generate a token for your account and save it to a .txt file

# you can type your email here or pass it as an argument
if len(sys.argv) > 1:
    email = sys.argv[1]
else:
    email = input("Enter your email: ")


options = webdriver.ChromeOptions()
options.add_argument("--headless")  # !uncomment when done testing
options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(options=options)

# Test name: final
# Step # | name | target | value
driver.get("https://poe.com/login?redirect_url=%2F")
assert "Poe" in driver.title
print("Page opened successfully.")

driver.set_window_size(839, 816)
print("Window size set successfully.")

driver.find_element(
    By.CSS_SELECTOR, ".Button_buttonBase__0QP_m:nth-child(5)").click()
print("Clicked on use email.")
time.sleep(3)

driver.find_element(By.CSS_SELECTOR, ".EmailInput_emailInput__4v_bn").click()
print("Clicked on email box.")
time.sleep(3)

driver.find_element(
    By.CSS_SELECTOR, ".EmailInput_emailInput__4v_bn").send_keys(email)
print("Email entered successfully.")
time.sleep(3)

driver.find_element(By.CSS_SELECTOR, ".Button_primary__pIDjn").click()
print("Clicked on Go.")
time.sleep(3)

driver.find_element(
    By.CSS_SELECTOR, ".VerificationCodeInput_verificationCodeInput__YD3KV").click()
print("Clicked on 6-digit box.")
time.sleep(3)

while True:
    code = input("Enter the verification code: ")
    if len(code) == 6 and code.isdigit():
        break
    print("Invalid verification code. Please enter a 6-digit number.")

driver.find_element(
    By.CSS_SELECTOR, ".VerificationCodeInput_verificationCodeInput__YD3KV").send_keys(code)
print("Verification code entered successfully.")
time.sleep(3)

driver.find_element(By.CSS_SELECTOR, ".Button_primary__pIDjn").click()
print("Clicked on login.")
time.sleep(1)

# Get token and save to a file
token = None
try:
    token = driver.get_cookie("p-b")["value"]
    with open("token.txt", "w") as f:
        f.write(token)
    print("Token saved successfully in token.txt.")
except Exception as e:
    print("Error occurred while retrieving or saving the token:", str(e))

client = poe.Client(token)
print("Login successful. Bots available:", client.get_bot_names())

driver.close()
