import yagmail

yag = yagmail.SMTP(
    "fawwazmuhammadarifin99@gmail.com",
    "pifbofhtiuxxjytj"
)

yag.send(
    to="fauzularifin99@gmail.com",
    subject="Test email",
    contents="Hello from Python"
)

print("Email sent")